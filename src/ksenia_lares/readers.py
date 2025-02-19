import datetime
from ksenia_lares.types_lares4 import BusPeripheral, BusPeripheralStatus, BusPeripheralType, DomusStatus, LinkStatus, Output, OutputStatus, Partition, Scenario, SystemArmStatus, SystemStatus, SystemTemperatureStatus, SystemTimeStatus, TemperatureStatus, ThermostatMode, ThermostatSeason, ThermostatStatus, Zone, ZoneBypass, ZoneStatus


def read_zones_status(payload: dict) -> list[Zone]:  
    return [
        Zone(
            id=int(zone["ID"]),
            status=ZoneStatus(zone["STA"]),
            bypass=ZoneBypass(zone["BYP"]),
            tamper=zone["T"],
            alarm=zone["A"],
            ohm=zone["OHM"],
            vas=zone["VAS"],
            label=zone["LBL"],
        )
        for zone in payload
    ]

def read_partitions_status(payload: dict) -> list[Partition]:
    return [
        Partition(
            id=int(partition["ID"]),
            armed=partition["ARM"],
            tamper=partition["T"],
            alarm=partition["AST"],
            test=partition["TST"],
        )
        for partition in payload
    ]

def read_outputs(payload: dict) -> list[Output]:
    return [
        Output(
            id=int(output["ID"]),
            description=output["DES"],
            cnv=output["CNV"],
            category=output["CAT"],
            mode=output["MOD"],
        )
        for output in payload
    ]

def read_peripherals(payload: dict) -> list[BusPeripheral]:
    return [
        BusPeripheral(
            id=int(peripheral["ID"]),
            type=BusPeripheralType(peripheral["TYP"]),
            description=peripheral["DES"]
            )
        for peripheral in payload
    ]

def read_outputs_status(payload: dict) -> list[OutputStatus]:
    return [
        OutputStatus(
            id=int(output["ID"]),
            status=output["STA"],
            position=(int(output["POS"]) if "POS" in output.keys()  else None),
            target_position=(int(output["TPOS"]) if "TPOS" in output.keys() else None),
        )
        for output in payload
    ]

def read_systems_status(payload: dict) -> list[SystemStatus]:
    systems_status = []    
    
    for system in payload:
        dusk =  system["TIME"]["DUSK"].split(':')
        dawn =  system["TIME"]["DAWN"].split(':')
        systems_status.append(
            SystemStatus(
                id=int(system["ID"]),
                informations=system["INFO"],
                tamper=system["TAMPER"],
                tamper_memory=system["TAMPER_MEM"],
                alarm=system["ALARM"],
                alarm_memory=system["ALARM_MEM"],
                fault=system["FAULT"],
                fault_memory=system["FAULT_MEM"],
                arm=SystemArmStatus(
                    mode=system["ARM"]["D"],
                    status=system["ARM"]["S"],
                ),
                temperature=SystemTemperatureStatus(
                    inside=float(system["TEMP"]["IN"]) if (system["TEMP"]["IN"] != 'NA') else None,
                    outside=float(system["TEMP"]["OUT"]) if (system["TEMP"]["OUT"] != 'NA') else None,
                ),
                time=SystemTimeStatus(
                    gmt=int(system["TIME"]["GMT"]),
                    timezone=int(system["TIME"]["TZ"]),
                    timezone_minutes=(system["TIME"]["TZM"]),
                    dawn=datetime.time(
                        hour=int(dawn[0]),
                        minute=int(dawn[1]),
                    ),
                    dusk=datetime.time(
                        hour=int(dusk[0]),
                        minute=int(dusk[1]),
                    ),
                ),
            )
        )
    
    return systems_status

def read_peripherals_status(payload: dict) -> list[BusPeripheralStatus]:
    return [
        BusPeripheralStatus(
            id=int(peripheral["ID"]),
            type=BusPeripheralType(peripheral["TYP"]),
            status=peripheral["STA"],
            bus=int(peripheral["BUS"]),
            link=LinkStatus(
                type=peripheral["LINK"]["TYPE"],
                serial_number=peripheral["LINK"]["SN"],
                bus=int(peripheral["LINK"]["BUS"]),
            ),
            domus=DomusStatus(
                temperature=float(peripheral["DOMUS"]["TEM"]),
                humidity=float(peripheral["DOMUS"]["HUM"]),
                light=float(peripheral["DOMUS"]["LHT"]),
            )
            if "DOMUS" in peripheral.keys()
            else None,
        )
        for peripheral in payload
    ]

def read_temperatures_status(payload: dict) -> list[TemperatureStatus]:
    temperatures = []
    
    for temperature in payload:
        thermostat_timer= temperature["THERM"]["TEMP_THR"]["VAL"].split(":") if temperature["THERM"]["TEMP_THR"]["VAL"] != 'NA' else None
        temperatures.append(
            TemperatureStatus(
                id=int(temperature["ID"]),
                temperature=float(temperature["TEMP"]),
                thermostat=ThermostatStatus(
                    season=ThermostatSeason(temperature["THERM"]["ACT_SEA"]),
                    mode=ThermostatMode(temperature["THERM"]["ACT_MODEL"]),
                    output=temperature["THERM"]["OUT_STATUS"],
                    timer=datetime.time(
                        hour=int(thermostat_timer[0]),
                        minute=int(thermostat_timer[1])
                        )
                        if thermostat_timer else None,
                )
            )
        )

    return temperatures

def read_scenarios(payload: dict) -> list[Scenario]:
    return [
        Scenario(
            id=int(scenario["ID"]),
            description=scenario["DES"],
            pin=scenario["PIN"],
            category=scenario["CAT"],
        )
        for scenario in payload
    ]