from dataclasses import dataclass
from enum import Enum
from sqlite3 import Time
from typing import Optional

class ZoneStatus(Enum):
    """Bypass of alarm zone."""

    READY = "R"
    ARMED = "A"

class ZoneBypass(Enum):
    """Bypass of alarm zone."""

    OFF = "NO"
    ON = "YES"

class Model(Enum):
    """Bypass of alarm zone."""

    LARES_4 = "lares4"
    BTICINO_4200 = "bticino4200"

class BusPeripheralType(Enum):
    DOMUS = "DOMUS"

class ThermostatSeason(Enum):
    """Thermostat season."""
    WINTER = "WIN"
    SUMMER = "SUM"

class ThermostatMode(Enum):
    """Thermostat mode."""
    OFF = "OFF"
    MANUAL = "MAN"
    MANUAL_TIMER = "MAN_TMR"
    WEEKLY = "WEEKLY"
    SPECIAL_1 = "SD1"
    SPECIAL_2 = "SD2"

class EventType(Enum):
    OUTPUTS = "STATUS_OUTPUTS"
    SYSTEMS = "STATUS_SYSTEM"
    PERIPHERALS = "STATUS_BUS_HA_SENSORS"
    TEMPERATURES = "STATUS_TEMPERATURES"
    ZONES = "STATUS_ZONES"
    PARTITIONS = "STATUS_PARTITIONS"

class ReadType(Enum):
    OUTPUTS = "OUTPUTS"
    PERIPHERALS = "BUS_HAS"
    SCENARIOS = "SCENARIOS"
    STATUS_OUTPUTS = "STATUS_OUTPUTS"
    STATUS_SYSTEMS = "STATUS_SYSTEM"
    STATUS_PERIPHERALS = "STATUS_BUS_HA_SENSORS"
    STATUS_TEMPERATURES = "STATUS_TEMPERATURES"
    STATUS_ZONES = "STATUS_ZONES"
    STATUS_PARTITIONS = "STATUS_PARTITIONS"

class ReadCallable(Enum):
    OUTPUTS = "read_outputs"
    BUS_HAS = "read_peripherals"
    SCENARIOS = "read_scenarios"
    STATUS_OUTPUTS = "read_outputs_status"
    STATUS_SYSTEM = "read_systems_status"
    STATUS_BUS_HA_SENSORS = "read_peripherals_status"
    STATUS_TEMPERATURES = "read_temperatures_status"
    STATUS_ZONES = "read_zones_status"
    STATUS_PARTITIONS = "read_partitions_status"

@dataclass
class Zone:
    """Alarm zone."""

    id: int
    status: ZoneStatus
    bypass: ZoneBypass
    tamper: str
    alarm: str
    ohm: str
    vas: str
    label: str 

    @property
    def enabled(self):
        return self.status == ZoneStatus.ARMED

@dataclass
class Partition:
    """Alarm partition."""

    id: int
    armed: str
    tamper: str
    alarm: str
    test: str

    @property
    def enabled(self):
        return self.armed != "D"
    
@dataclass
class Scenario:
    """Alarm scenario."""

    id: int
    description: str
    pin: str
    category: str

@dataclass
class Output:
    """Output."""
    id: int
    description: str
    cnv: str
    category: str
    mode: str

@dataclass
class BusPeripheral:
    """Bus peripheral."""
    id: int
    description: str
    type: BusPeripheralType

@dataclass
class OutputStatus:
    """Output status."""
    id: int
    status: str
    position: Optional[int] = None
    target_position: Optional[int] = None

@dataclass
class SystemArmStatus:
    """System status."""
    mode: str
    status: str

@dataclass
class SystemTemperatureStatus:
    """System status."""
    inside: Optional[float] = None
    outside: Optional[float] = None

@dataclass
class SystemTimeStatus:
    """System status."""
    gmt: int
    timezone: int
    timezone_minutes: int
    dawn: Time
    dusk: Time

@dataclass
class SystemStatus:
    """System status."""
    id: int
    informations: list
    tamper: list
    tamper_memory: list
    alarm: list
    alarm_memory: list
    fault: list
    fault_memory: list
    arm: SystemArmStatus
    temperature: SystemTemperatureStatus
    time: SystemTimeStatus

@dataclass
class LinkStatus:
    type: str
    serial_number: str
    bus: int

@dataclass
class DomusStatus:
    temperature: float
    humidity: float
    light: float

@dataclass
class BusPeripheralStatus:
    """Bus peripheral status."""
    id: int
    type: BusPeripheralType
    status: str
    bus: int
    link: LinkStatus
    domus: Optional[DomusStatus] = None

@dataclass
class ThermostatStatus:
    """Thermostat status."""
    season: ThermostatSeason
    mode: ThermostatMode
    output: str
    timer: Optional[Time] = None

@dataclass
class TemperatureStatus:
    """Temperature status."""
    id: int
    temperature: float
    thermostat: ThermostatStatus