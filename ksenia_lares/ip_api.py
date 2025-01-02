import logging
from typing import List

from getmac import get_mac_address
import aiohttp
from lxml import etree

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
        self._zone_descriptions = None
        self._partition_descriptions = None
        self._scenario_descriptions = None

    async def info(self) -> dict[str, str] | None:
        """Get general info"""
        response = await self._get("info/generalInfo.xml")

        if response is None:
            return None

        mac = get_mac_address(ip=self._ip)
        unique_id = str(mac)

        if mac is None:
            # Fallback to IP addresses when MAC cannot be determined
            unique_id = f"{self._ip}:{self._port}"

        info = {
            "mac": mac,
            "id": unique_id,
            "name": response.xpath("/generalInfo/productName")[0].text,
            "info": response.xpath("/generalInfo/info1")[0].text,
            "version": response.xpath("/generalInfo/productHighRevision")[0].text,
            "revision": response.xpath("/generalInfo/productLowRevision")[0].text,
            "build": response.xpath("/generalInfo/productBuildRevision")[0].text,
        }

        return info

    async def device_info(self) -> dict | None:
        """Get device info"""
        device_info = await self.info()

        if device_info is None:
            return None

        return {
            "id": device_info["id"],
            "name": device_info["name"],
            "model": device_info["name"],
            "sw_version": f'{device_info["version"]}.{device_info["revision"]}.{device_info["build"]}',
            "configuration_url": self._host,
            "MAC": device_info["mac"]
        }

    async def zone_descriptions(self):
        """Get available zones"""
        model = await self.get_model()
        if self._zone_descriptions is None:
            self._zone_descriptions = await self._get_descriptions(
                f"zones/zonesDescription{model}.xml", "/zonesDescription/zone"
            )

        return self._zone_descriptions

    async def zones(self):
        """Get available zones"""
        model = await self.get_model()
        response = await self._get(f"zones/zonesStatus{model}.xml")

        if response is None:
            return None

        zones = response.xpath("/zonesStatus/zone")

        return [
            {
                "status": zone.find("status").text,
                "bypass": zone.find("bypass").text,
            }
            for zone in zones
        ]

    async def partition_descriptions(self):
        """Get available partitions"""
        model = await self.get_model()

        if self._partition_descriptions is None:
            self._partition_descriptions = await self._get_descriptions(
                f"partitions/partitionsDescription{model}.xml",
                "/partitionsDescription/partition",
            )

        return self._partition_descriptions

    async def partitions(self):
        """Get status of partitions"""
        model = await self.get_model()
        response = await self._get(f"partitions/partitionsStatus{model}.xml")

        if response is None:
            return None

        partitions = response.xpath("/partitionsStatus/partition")

        return [
            {
                "status": partition.text,
            }
            for partition in partitions
        ]

    async def scenarios(self):
        """Get status of scenarios"""
        response = await self._get("scenarios/scenariosOptions.xml")

        if response is None:
            return None

        scenarios = response.xpath("/scenariosOptions/scenario")

        return [
            {
                "id": idx,
                "enabled": scenario.find("abil").text == "TRUE",
                "noPin": scenario.find("nopin").text == "TRUE",
            }
            for idx, scenario in enumerate(scenarios)
        ]

    async def scenario_descriptions(self):
        """Get descriptions of scenarios"""
        if self._scenario_descriptions is None:
            self._scenario_descriptions = await self._get_descriptions(
                "scenarios/scenariosDescription.xml", "/scenariosDescription/scenario"
            )

        return self._scenario_descriptions

    async def activate_scenario(self, scenario: int, code: str) -> bool:
        """Activate the given scenarios, requires the alarm code"""
        params = {"macroId": scenario}

        return await self._send_command("setMacro", code, params)

    async def bypass_zone(self, zone: int, code: str, bypass: bool) -> bool:
        """Activate the given scenarios, requires the alarm code"""
        params = {
            "zoneId": zone + 1,  # Lares uses index starting with 1
            "zoneValue": 1 if bypass else 0,
        }

        return await self._send_command("setByPassZone", code, params)

    async def get_model(self) -> str:
        """Get model information"""
        if self._model is None:
            info = await self.info()
            if info is None:
                raise RuntimeError("Unable to get info of device")

            if info["name"].endswith("128IP"):
                self._model = "128IP"
            elif info["name"].endswith("48IP"):
                self._model = "48IP"
            else:
                self._model = "16IP"

        return self._model

    async def _send_command(
        self, command: str, code: str, params: dict[str, int]
    ) -> bool:
        """Send Command"""
        urlparam = "".join(f"&{k}={v}" for k, v in params.items())
        path = f"cmd/cmdOk.xml?cmd={command}&pin={code}&redirectPage=/xml/cmd/cmdError.xml{urlparam}"

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
                    xml = await response.text()
                    content: etree.ElementBase = etree.fromstring(xml, parser=None)
                    return content

        except aiohttp.ClientConnectorError as conn_err:
            _LOGGER.warning("Host %s: Connection error %s", self._host, str(conn_err))
            raise ConnectionError("Connector error while getting information from Lares alarm.")
        except:  # pylint: disable=bare-except
            _LOGGER.warning("Host %s: Unknown exception occurred", self._host)
            raise ConnectionError("Unkown error while getting information from Lares alarm.")
    
    async def _get_descriptions(self, path: str, element: str) -> List[str] | None:
        """Get descriptions"""
        response = await self._get(path)
        content = response.xpath(element)
        descriptions: List[str] = [item.text for item in content if item.text is not None]
    
        return descriptions
