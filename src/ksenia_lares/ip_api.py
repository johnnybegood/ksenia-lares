import logging
from typing import List, Optional
from getmac import get_mac_address
import aiohttp
from lxml import etree

from .types_ip import (
    AlarmInfo,
    Command,
    Partition,
    PartitionStatus,
    Scenario,
    Zone as ZoneIP,
    ZoneBypass,
    ZoneStatus,
)
from .types_lares4 import (
    Zone as ZoneLares4
)
from .base_api import BaseApi

_LOGGER = logging.getLogger(__name__)


class IpAPI(BaseApi):
    """Implementation for the IP range of Kseni Lares (Lare 16 IP, 48 IP & 128 IP)."""

    def __init__(self, data: dict) -> None:
        """
        Initialize the API with the necessary connection details.

        Args:
            data (dict): A dictionary containing the following keys:
                - username (str): The username for authentication.
                - password (str): The password for authentication.
                - host (str): The hostname or IP address of the API.
                - port (int): The port number of the API.

        Raises:
            ValueError: If any required parameter is missing or invalid.
        """
        if not all(key in data for key in ("username", "password", "host", "port")):
            raise ValueError(
                "Missing required parameter(s): username, password, host, or port."
            )

        self._auth = aiohttp.BasicAuth(data["username"], data["password"])
        self._ip = data["host"]
        self._port = data["port"]
        self._host = f"http://{self._ip}:{self._port}"
        self._model = None
        self._description_cache = {}

    async def info(self) -> AlarmInfo:
        """
        Get info about the alarm system, like name and version.

        Returns:
            AlarmInfo: General information about the alarm system.
        """
        response = await self._get("info/generalInfo.xml")
        mac = get_mac_address(ip=self._ip)

        info: AlarmInfo = {
            "mac": mac,
            "host": f"{self._ip}:{self._port}",
            "name": response.xpath("/generalInfo/productName")[0].text,
            "info": response.xpath("/generalInfo/info1")[0].text,
            "version": response.xpath("/generalInfo/productHighRevision")[0].text,
            "revision": response.xpath("/generalInfo/productLowRevision")[0].text,
            "build": response.xpath("/generalInfo/productBuildRevision")[0].text,
        }

        return info

    async def get_zones(self) -> List[ZoneIP]:
        """
        Get status of all zones.

        Returns:
            List[Zone]: List of the zones in the alarm system.
        """
        model = await self.get_model()
        response = await self._get(f"zones/zonesStatus{model}.xml")
        zones = response.xpath("/zonesStatus/zone")
        descriptions: List[str] = await self._get_descriptions(
            f"zones/zonesDescription{model}.xml", "/zonesDescription/zone"
        )

        return [
            ZoneIP(
                id=index,
                description=descriptions[index],
                status=ZoneStatus(zone.find("status").text),
                bypass=ZoneBypass(zone.find("bypass").text),
            )
            for index, zone in enumerate(zones)
        ]

    async def get_partitions(self) -> List[Partition]:
        """
        Get status of partitions.

        Returns:
            List[Partition]: List of the partitions in the alarm system.
        """
        model = await self.get_model()
        response = await self._get(f"partitions/partitionsStatus{model}.xml")
        partitions = response.xpath("/partitionsStatus/partition")
        descriptions: List[str] = await self._get_descriptions(
            f"partitions/partitionsDescription{model}.xml",
            "/partitionsDescription/partition",
        )

        return [
            Partition(
                id=index,
                description=descriptions[index],
                status=PartitionStatus(partition.text),
            )
            for index, partition in enumerate(partitions)
        ]

    async def get_scenarios(self) -> List[Scenario]:
        """
        Get status of scenarios

        Returns:
            List[Scenario]: List of the scenarios in the alarm system.
        """
        response = await self._get("scenarios/scenariosOptions.xml")
        scenarios = response.xpath("/scenariosOptions/scenario")
        descriptions: List[str] = await self._get_descriptions(
            "scenarios/scenariosDescription.xml",
            "/scenariosDescription/scenario",
        )

        return [
            Scenario(
                id=index,
                description=descriptions[index],
                enabled=scenario.find("abil").text.upper() == "TRUE",
                no_pin=scenario.find("nopin").text.upper() == "TRUE",
            )
            for index, scenario in enumerate(scenarios)
        ]

    async def activate_scenario(
        self, scenario: int | Scenario, pin: Optional[str]
    ) -> bool:
        """
        Active the given scenario on the alarm. Can be used to arm or disarm the alarm.

        Args:
            scenario (int | Scenario): Thescenario to activate, by ID or from a retrieved scenario
            pin (Optional[str]): The pin code for the alarm, if the scenario doesn't have `no_pin` set, this is required.

        Returns:
            bool: `True` when the scenario is actived, `False` if any issue occured.
        """

        if isinstance(scenario, int):
            scenarios = await self.get_scenarios()
            current = next(item for item in scenarios if item.id == scenario)
        elif isinstance(scenario, Scenario):
            current = scenario  # We trust the data given, the alarm will refuse to execute when PIN is needed and no PIN is available
        else:
            raise TypeError("Input must be an int (scenario ID) or a Scenario object")

        # Validate if PIN is required
        if pin is None and not current.no_pin:
            raise ValueError(f"PIN is required for scenario {current.description}")

        params = {"macroId": current.id}
        return await self._send_command(Command.SET_MACRO, pin, params)

    async def bypass_zone(self, zone: int | ZoneIP | ZoneLares4, pin: str, bypass: ZoneBypass) -> bool:
        """
        Activates or deactivates the bypass on the given zone.

        Args:
            zone (int | Zone): The zone or id of the zone to (un)bypass.
            pin (str): PIN code, required for bypass.
            bypass (ZoneBypass): Set to bypass or unbypass zone.

        Returns:
            bool: True if the (un)bypass was executed successfully.
        """

        if isinstance(zone, ZoneIP):
            zone_id = zone.id
        elif isinstance(zone, int):
            zone_id = zone
        else:
            raise TypeError("Zone must be an int (zone ID) or a Zone object")

        params = {
            "zoneId": zone_id + 1,  # Lares uses index starting with 1
            "zoneValue": 1 if bypass == ZoneBypass.ON else 0,
        }

        return await self._send_command(Command.SET_BYPASS, pin, params)

    async def get_model(self) -> str:
        """
        Get model of the alarm system

        Returns:
            str: The model of the alarm system (128IP, 48IP or 16IP)
        """
        if self._model is None:
            info = await self.info()

            if info["name"].endswith("128IP"):
                self._model = "128IP"
            elif info["name"].endswith("48IP"):
                self._model = "48IP"
            else:
                self._model = "16IP"

        return self._model

    async def _send_command(
        self, command: Command, pin: Optional[str], params: dict[str, int]
    ) -> bool:
        """
        Send command to alarm.

        Args:
            command (Command): The command to send.
            pin (Optional[str]): Optional PIN code, might be required by the specific command.
            params (dict[str, int]): Additional parameters for the command.

        Returns:
            bool: True if the command executed successfully.
        """

        urlparam = "".join(f"&{k}={v}" for k, v in params.items())
        path = f"cmd/cmdOk.xml?cmd={command.value}&redirectPage=/xml/cmd/cmdError.xml{urlparam}"

        if pin is not None:
            path += f"&pin={pin}"
            _LOGGER.debug("Sending command %s", path.replace(pin, "PIN"))
        else:
            _LOGGER.debug("Sending command %s", path)

        response = await self._get(path)
        cmd = response.xpath("/cmd")

        if cmd is None or cmd[0].text != "cmdSent":
            _LOGGER.error("Command send failed: %s", response)
            return False

        return True

    async def _get(self, path) -> etree.ElementBase:
        """Generic send method."""
        url = f"{self._host}/xml/{path}"

        try:
            async with aiohttp.ClientSession(auth=self._auth) as session:
                async with session.get(url=url) as response:
                    if response.status != 200:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"Request failed with status {response.status}: {await response.text()}",
                        )

                    xml = await response.text()
                    content: etree.ElementBase = etree.fromstring(xml, parser=None)
                    return content

        except aiohttp.ClientConnectorError as conn_err:
            _LOGGER.warning("Host %s: Connection error %s", self._host, str(conn_err))
            raise ConnectionError(
                "Connector error while getting information from Lares alarm."
            )
        except BaseException as e:
            _LOGGER.warning("Host %s: Unknown exception occurred", self._host)
            raise e

    async def _get_descriptions(self, path: str, element: str) -> List[str]:
        """Get descriptions"""
        if path in self._description_cache:
            return self._description_cache[path]

        response = await self._get(path)
        content = response.xpath(element)
        descriptions: List[str] = [item.text for item in content]

        self._description_cache[path] = descriptions
        return descriptions
