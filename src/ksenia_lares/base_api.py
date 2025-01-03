from abc import ABC, abstractmethod
from typing import List
from ksenia_lares.types import AlarmInfo, Partition, Zone

"""Base API for the Ksenia Lares"""


class BaseApi(ABC):

    @abstractmethod
    async def info(self) -> AlarmInfo:
        """Get info about the alarm system, like name and version"""
        pass

    @abstractmethod
    async def get_zones(self) -> List[Zone]:
        """Get status of alarm zones"""
        pass

    @abstractmethod
    async def activate_scenario(self, scenario: int, code: str) -> bool:
        """Activate the given scenarios, requires the alarm code"""
        pass

    @abstractmethod
    async def get_partitions(self) -> List[Partition]:
        """Get status of alarm partitions"""
        pass
