from abc import ABC, abstractmethod
from typing import List
from ksenia_lares.types import AlarmInfo, Zone, ZoneStatus

"""Base API for the Ksenia Lares"""


class BaseApi(ABC):

    @abstractmethod
    async def info(self) -> AlarmInfo:
        """Get info about the alarm system, like name and version"""
        pass

    @abstractmethod
    async def get_zones(self) -> List[Zone]:
        """Get status of all zones"""

    @abstractmethod
    async def activate_scenario(self, scenario: int, code: str) -> bool:
        """Activate the given scenarios, requires the alarm code"""
        pass
