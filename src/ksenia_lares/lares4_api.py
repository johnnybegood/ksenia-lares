import datetime
from operator import ge
import aiohttp
import json
import ssl
import time
import asyncio

from typing import Callable, List

import ksenia_lares
from ksenia_lares.readers import read_outputs, read_outputs_status, read_partitions_status, read_peripherals, read_peripherals_status, read_scenarios, read_systems_status, read_temperatures_status, read_zones_status
import ksenia_lares.readers

from .types_lares4 import BusPeripheral, BusPeripheralStatus, BusPeripheralType, DomusStatus, EventType, LinkStatus, Model, Output, OutputStatus, ReadCallable, ReadType, SystemArmStatus, SystemStatus, SystemTemperatureStatus, SystemTimeStatus, TemperatureStatus, ThermostatMode, ThermostatSeason, ThermostatStatus, Zone, ZoneBypass, ZoneStatus, Partition, Scenario


def u(e):
    t = []
    for n in range(0, len(e)):
        r = ord(e[n])
        if r < 128:
            t.append(r)
        else:
            if r < 2048:
                t.append(192 | r >> 6)
                t.append(128 | 63 & r)
            else:
                if r < 55296 or r >= 57344:
                    t.append(224 | r >> 12)
                    t.append(128 | r >> 6 & 63)
                    t.append(128 | 63 & r)
                else:
                    n = n + 1
                    r = 65536 + ((1023 & r) << 10 | 1023 & ord(e[n]))
                    t.append(240 | r >> 18)
                    t.append(128 | r >> 12 & 63)
                    t.append(128 | r >> 6 & 63)
                    t.append(128 | 63 & r)
        n = n + 1

    return t

def crc16(e):
    i = u(e)
    l = e.rfind('"CRC_16"') + len('"CRC_16"') + (len(i) - len(e))
    r = 65535
    s = 0
    while s < l:
        t = 128
        o = i[s]
        while t:
            if 32768 & r:
                n = 1
            else:
                n = 0
            r <<= 1
            r &= 65535
            if o & t:
                r = r + 1
            if n:
                r = r ^ 4129
            t >>= 1
        s = s + 1
    return "0x" + format(r, "04x")

def get_ssl_context():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
    return ctx

class CommandFactory:
    def __init__(self, sender: str, pin: str) -> None:
        self._command_id = 0
        self._sender = sender
        self._pin = pin

    def get_sender(self) -> str:
        return self._sender

    def get_login_id(self) -> str:
        return self._login_id

    def set_login_id(self, login_id: str) -> None:
        self._login_id = login_id

    def get_pin(self) -> str:
        return self._pin

    def get_current_command_id(self) -> int:
        return self._command_id

    def get_next_command_id(self) -> int:
        self._command_id += 1
        return self._command_id

    def build_payload(self, payload: dict) -> dict:
        return {
            **payload,
            **({"ID_LOGIN": self.get_login_id()} if "ID_LOGIN" in payload else {}),
            **({"PIN": self.get_pin()} if "PIN" in payload else {}),
        }

    def build_command(self, cmd: str, payload_type: str, payload: dict) -> dict:
        timestamp = str(int(time.time()))

        command = {
            "SENDER": self.get_sender(),
            "RECEIVER": "",
            "CMD": cmd,
            "ID": f"{self.get_next_command_id()}",
            "PAYLOAD_TYPE": payload_type,
            "PAYLOAD": self.build_payload(payload),
            "TIMESTAMP": f"{timestamp}",
            "CRC_16": "0x0000",
        }

        command["CRC_16"] = crc16(json.dumps(command))

        return command

class Lares4API:
    def __init__(self, data, model: Model = Model.LARES_4):
        if not all(key in data for key in ("url", "pin", "sender")):
            raise ValueError(
                "Missing one or more of the following keys: host, pin, sender"
            )
        self.url = data["url"]
        self.host = f"wss://{data['url']}/KseniaWsock"
        self.model = model
        self.command_factory = CommandFactory(data["sender"], data["pin"])
        self.is_running = False

        self.event_listeners: dict[EventType, list[Callable]] = {}

    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(
            self.host, protocols=["KS_WSOCK"], ssl_context=get_ssl_context()
        )
        print(f"Connected to {self.url}")
        self.is_running = True
                
    async def command(self, cmd: str, payload_type: str, payload: dict) -> dict | None:
        send_command = asyncio.create_task(self.send_command(cmd, payload_type, payload))
        receive_command = asyncio.create_task(self.receive_command())
        _, response = await asyncio.gather(send_command, receive_command)
        return response 
        
    async def send_command(self, cmd: str, payload_type: str, payload: dict):
        if self.ws:
            command = self.command_factory.build_command(cmd, payload_type, payload)
            print(f"Sending command: {command}")
            await self.ws.send_json(command)
        else:
            raise Exception("WebSocket is not connected")
        
    async def receive_command(self) -> dict | None:
        if self.ws:
            msg = await self.ws.receive_json()
            return msg
        else:
            raise Exception("WebSocket is not connected")
        
    async def get(self, read_types: list[ReadType]) -> list[dict]:
        await self.send_command(
            "READ",
            "MULTI_TYPES",
            {
                "ID_LOGIN": True,
                "ID_READ": "1",
                "TYPES": [read_type.value for read_type in read_types]
            }
        )

        results = []
        response = await self.receive_command()
        
        if response and response["PAYLOAD"]["RESULT"] == "OK":
            for read_type in read_types:
                print(f"Reading {read_type.value}")
                print(ReadCallable[read_type.value])
                callable = getattr(ksenia_lares.readers, ReadCallable[read_type.value].value)
                results.append(callable(response["PAYLOAD"][read_type.value]))

        return results

    async def receive_commands(self, len = 1):
        results = []

        if self.ws:
            for _ in range(len):
                msg = await self.ws.receive_json()
                print(f"Received command: {msg}")
                results.append(msg)
            return results
        else:
            raise Exception("WebSocket is not connected")

    async def close(self):
        self.is_running = False
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()

    async def login(self):
        send_login = asyncio.create_task(self.send_login())
        receive_login = asyncio.create_task(self.receive_login())
        await asyncio.gather(send_login, receive_login)

    async def send_login(self):
        await self.send_command(
            "LOGIN",
            "UNKNOWN" if self.model == Model.LARES_4 else "USER",
            { "PIN": True }
        )

    async def receive_login(self, timeout: float = 0.7):
        if self.ws:
            msg = await asyncio.wait_for(self.ws.receive(), timeout=timeout)
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data["CMD"] == "LOGIN_RES":
                    self.command_factory.set_login_id(data["PAYLOAD"]["ID_LOGIN"])
                else:
                    raise Exception("Login failed")
        else:
            raise Exception("WebSocket is not connected")

    async def get_zones(self) -> List[Zone]:
        zones_response = await self.get([ReadType.STATUS_ZONES])
        if zones_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_zones_status(zones_response[0]["PAYLOAD"][ReadType.STATUS_ZONES.value])
        else:
            raise Exception("Failed to get zones")
    
    async def get_partitions(self) -> List[Partition]:
        partitions_response = await self.get([ReadType.STATUS_PARTITIONS])
        if partitions_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_partitions_status(partitions_response[0]["PAYLOAD"][ReadType.STATUS_PARTITIONS.value])
        else:
            raise Exception("Failed to get partitions")

    async def get_scenarios(self):
        scenarios_response = await self.get([ReadType.SCENARIOS])
        if scenarios_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_scenarios(scenarios_response[0]["PAYLOAD"][ReadType.SCENARIOS.value])
        else:
            raise Exception("Failed to get scenarios")

    async def get_outputs(self) -> list[Output]:
        outputs_response = await self.get([ReadType.OUTPUTS])
        if outputs_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_outputs(outputs_response[0]["PAYLOAD"][ReadType.OUTPUTS.value])
        else:
            raise Exception("Failed to get outputs")
    
    async def get_peripherals(self) -> List[BusPeripheral]:
        bus_peripherals_response = await self.get([ReadType.PERIPHERALS])
        if bus_peripherals_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_peripherals(bus_peripherals_response[0]["PAYLOAD"][ReadType.PERIPHERALS.value])
        else:
            raise Exception("Failed to get bus peripherals")
    
    async def get_outputs_status(self) -> list[OutputStatus]:
        outputs_status_response = await self.get([ReadType.STATUS_OUTPUTS])
        if outputs_status_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_outputs_status(outputs_status_response[0]["PAYLOAD"][ReadType.STATUS_OUTPUTS.value])
        else:
            raise Exception("Failed to get outputs status")
    
    async def get_systems_status(self) -> list[SystemStatus]:
        systems_status_response = await self.get([ReadType.STATUS_SYSTEMS])
        if systems_status_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_systems_status(systems_status_response[0]["PAYLOAD"][ReadType.STATUS_SYSTEMS.value])
        else:
            raise Exception("Failed to get systems status")

    async def get_peripherals_status(self) -> List[BusPeripheralStatus]:
        peripherals_status_response = await self.get([ReadType.STATUS_PERIPHERALS])
        if peripherals_status_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_peripherals_status(peripherals_status_response[0]["PAYLOAD"][ReadType.STATUS_PERIPHERALS.value])
        else:
            raise Exception("Failed to get peripherals status")
    
    async def get_temperatures_status(self) -> List[TemperatureStatus]:
        temperatures_status_response = await self.get([ReadType.STATUS_TEMPERATURES])
        if temperatures_status_response[0]["PAYLOAD"]["RESULT"] == "OK":
            return read_temperatures_status(temperatures_status_response[0]["PAYLOAD"][ReadType.STATUS_TEMPERATURES.value])
        else:
            raise Exception("Failed to get temperatures status")

    async def activate_scenario(self, scenario_id):
        scenario = await self.command(
            "CMD_USR",
            "CMD_EXE_SCENARIO",
            {
                "ID_LOGIN": True,
                "PIN": True,
                "SCENARION": {
                    "ID": scenario_id,
                },
            },
        )

        return scenario

    async def bypass_zone(self, zone: int | Zone, zone_bypass: ZoneBypass) -> bool:
        bypass_zone = await self.command(
            "CMD_USR",
            "CMD_BYP_ZONE",
            {
                "ID_LOGIN": True,
                "PIN": True,
                "ZONE": {
                    "ID": zone.id if isinstance(zone, Zone) else zone,
                    "BYP": zone_bypass,
                },
            },
        )
        if bypass_zone:
            return bypass_zone["PAYLOAD"]["RESULT"] == "OK"
        return False
    
    async def setOutput(self, id: int, value: str | int) -> bool:
        set_output = await self.command(
            "CMD_USR",
            "CMD_SET_OUTPUT",
            {
                "ID_LOGIN": True,
                "PIN": True,
                "OUTPUT": {
                    "ID": str(id),
                    "VAL": str(value),
                },
            },
        )
        if set_output:
            return set_output["PAYLOAD"]["RESULT"] == "OK"
        return False
    
    async def add_event_listener(self, event: EventType, event_listener: Callable[[str], None]) -> None:
        """Add event listener."""
        register_event_response = await self.send_command(
            "REALTIME",
            "REGISTER",
            {"ID_LOGIN": True, "TYPES": [event.value]},
        )

        if register_event_response and register_event_response["PAYLOAD"]["RESULT"] == "OK":
            if event not in self.event_listeners.keys():
                self.event_listeners[event] = []
            self.event_listeners[event].append(event_listener)
        else:
            raise Exception("Failed to register event listener")
        
    def remove_event_listener(self, event: EventType, event_listener: Callable[[str], None]) -> None:
        """Remove event listener."""
        if event in self.event_listeners:
            self.event_listeners[event].remove(event_listener)
            if not self.event_listeners[event]:
                del self.event_listeners[event]

    async def listen(self) -> None:
        """Start listening for events."""
        if not self.ws:
            raise Exception("WebSocket is not connected")
        
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data["PAYLOAD_TYPE"] == "CHANGES":
                    if self.command_factory._sender in data["PAYLOAD"].keys():
                        for event in self.event_listeners.keys():
                            if event.value in data["PAYLOAD"][self.command_factory._sender].keys():
                                for listener in self.event_listeners[event]:
                                    listener(data["PAYLOAD"][self.command_factory._sender][event.value])

    async def logout(self) -> None:
        logout_response = await self.command(
            "LOGOUT",
            "USER",
            {"ID_LOGIN": True},
        )

        if logout_response and logout_response["CMD"] == "LOGOUT_RES":
            await self.close()
        else:
            raise Exception("Failed to logout")