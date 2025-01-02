from abc import ABC, abstractmethod

"""Base API for the Ksenia Lares"""
class BaseApi(ABC):
    
    @abstractmethod
    async def info(self) -> dict | None:
        """Retrieve general information."""
        pass

    @abstractmethod
    async def device_info(self) -> dict | None:
        """Retrieve detailed device information."""
        pass

    @abstractmethod
    async def get_model(self) -> str:
        """Retrieve model information."""
        pass

    @abstractmethod
    async def activate_scenario(self, scenario: int, code: str) -> bool:
        """Activate the given scenarios, requires the alarm code"""
        pass
