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


@dataclass
class Zone:
    """Alarm zone (without description)."""

    id: str
    description: str
    status: ZoneStatus
    bypass: str
