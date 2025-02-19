from abc import ABC, abstractmethod
from typing import List, Optional
from ksenia_lares.types_ip import AlarmInfo, Partition, Scenario, Zone, ZoneBypass

class BaseApi(ABC):
    """Base API for the Ksenia Lares"""

    @abstractmethod
    async def info(self) -> AlarmInfo:
        """
        Get info about the alarm system, like name and version.

        Returns:
            AlarmInfo: General information about the alarm system.
        """
        pass

    @abstractmethod
    async def get_zones(self) -> List[Zone]:
        """
        Get status of all zones.

        Returns:
            List[Zone]: List of the zones in the alarm system.
        """
        pass

    @abstractmethod
    async def get_partitions(self) -> List[Partition]:
        """
        Get status of partitions.

        Returns:
            List[Partition]: List of the partitions in the alarm system.
        """
        pass

    @abstractmethod
    async def get_scenarios(self) -> List[Scenario]:
        """
        Get status of scenarios

        Returns:
            List[Scenario]: List of the scenarios in the alarm system.
        """
        pass

    @abstractmethod
    async def activate_scenario(
        self, scenario: int | Scenario, pin: Optional[str]
    ) -> bool:
        """
        Active the given scenario on the alarm. Can be used to arm or disarm the alarm.

        Args:
            scenario (int | Scenario): Thescenario to activate, by ID or from a retrieved scenario
            pin (Optional[str]): The pin code for the alarm, if the scenario doesn't have `NoPin` set, this is required.

        Returns:
            bool: `True` when the scenario is actived, `False` if any issue occured.
        """
        pass

    @abstractmethod
    async def bypass_zone(self, zone: int | Zone, pin: str, bypass: ZoneBypass) -> bool:
        """
        Activates or deactivates the bypass on the given zone.

        Args:
            zone (int | Zone): The zone or id of the zone to (un)bypass.
            pin (str): PIN code, required for bypass.
            bypass (ZoneBypass): Set to bypass or unbypass zone.

        Returns:
            bool: True if the (un)bypass was executed successfully.
        """
