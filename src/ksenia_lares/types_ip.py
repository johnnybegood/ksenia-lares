from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypedDict

class AlarmInfo(TypedDict):
    mac: Optional[str]
    host: str
    name: str
    info: str
    version: str
    revision: str
    build: str


class ZoneStatus(Enum):
    """Status of alarm zone."""

    ALARM = "ALARM"
    NORMAL = "NORMAL"
    NOT_USED = "NOT_USED"


class ZoneBypass(Enum):
    """Bypass of alarm zone."""

    OFF = "UN_BYPASS"
    ON = "BYPASS"

@dataclass
class Zone:
    """Alarm zone."""

    id: int
    description: str
    status: ZoneStatus
    bypass: ZoneBypass

    @property
    def enabled(self):
        return self.description is not None


class PartitionStatus(Enum):
    """Status of alarm partition."""

    DISARMED = "DISARMED"
    ARMED = "ARMED"
    ARMED_IMMEDIATE = "ARMED_IMMEDIATE"
    ARMING = "EXIT"
    PENDING = "PREALARM"
    ALARM = "ALARM"


@dataclass
class Partition:
    """Alarm partition."""

    id: int
    description: str
    status: PartitionStatus

    @property
    def enabled(self):
        return self.description is not None


@dataclass
class Scenario:
    """Alarm scenario."""

    id: int
    description: str
    enabled: bool
    no_pin: bool


class Command(Enum):
    "Alarm commands."

    SET_MACRO = "setMacro"
    SET_BYPASS = "setByPassZone"
