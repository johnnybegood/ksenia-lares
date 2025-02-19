from unittest.mock import patch
from aiohttp import ClientError
import pytest
from aioresponses import aioresponses
from ksenia_lares import IpAPI
from ksenia_lares.types_ip import PartitionStatus, Scenario, Zone, ZoneBypass, ZoneStatus


@pytest.fixture
def mock_config():
    return {
        "username": "test_user",
        "password": "test_pass",
        "host": "192.168.1.1",
        "port": 8080,
    }


@pytest.fixture
def mock_xml_responses():
    return {
        "info/generalInfo.xml": """
        <generalInfo>
            <productName>Mock Alarm 128IP</productName>
            <info1>Mock Info</info1>
            <productHighRevision>1.0</productHighRevision>
            <productLowRevision>2</productLowRevision>
            <productBuildRevision>3</productBuildRevision>
        </generalInfo>
        """,
        "zones/zonesStatus128IP.xml": """
        <zonesStatus>
            <zone>
                <status>NORMAL</status>
                <bypass>UN_BYPASS</bypass>
            </zone>
            <zone>
                <status>ALARM</status>
                <bypass>BYPASS</bypass>
            </zone>
            <zone>
                <status>NOT_USED</status>
                <bypass>UN_BYPASS</bypass>
            </zone>
        </zonesStatus>
        """,
        "zones/zonesDescription128IP.xml": """
        <zonesDescription>
            <zone>Description 1</zone>
            <zone>Description 2</zone>
            <zone></zone>
        </zonesDescription>
        """,
        "partitionsDescription.xml": """
        <partitionsDescription>
            <partition>Description 1</partition>
            <partition></partition>
        </partitionsDescription>
        """,
        "partitionsStatus.xml": """
        <partitionsStatus>
            <partition>ARMED</partition>
            <partition>DISARMED</partition>
        </partitionsStatus>
        """,
        "scenariosDescription.xml": """
        <scenariosDescription>
            <scenario>Turn off</scenario>
            <scenario>Alarm on</scenario>
            <scenario>Scenario</scenario>
        </scenariosDescription>
        """,
        "scenariosOptions.xml": """
        <scenariosOptions>
            <scenario>
                <abil>TRUE</abil>
                <nopin>TRUE</nopin>
            </scenario>
            <scenario>
                <abil>TRUE</abil>
                <nopin>FALSE</nopin>
            </scenario>
            <scenario>
                <abil>FALSE</abil>
                <nopin>FALSE</nopin>
            </scenario>
        </scenariosOptions>
        """,
        "CommandSuccess": """
        <cmd>cmdSent</cmd>        
        """,
        "CommandFailed": """
        <cmd>Command failed, error error error</cmd>        
        """,
    }


@pytest.mark.asyncio
async def test_info_standard_response(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/info/generalInfo.xml",
            body=mock_xml_responses["info/generalInfo.xml"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)
        info = await api.info()

        assert info["name"] == "Mock Alarm 128IP"
        assert info["version"] == "1.0"
        assert info["revision"] == "2"
        assert info["build"] == "3"


@pytest.mark.asyncio
async def test_info_has_mac(mock_config, mock_xml_responses):
    # Direct mock of get_mac_address doesn't seem to work, used this sample from their tests
    with patch(
        "getmac.getmac.get_by_method", return_value="00:01:02:04:00:12"
    ) as mock_get_mac_address:
        with aioresponses() as mocked:
            mocked.get(
                "http://192.168.1.1:8080/xml/info/generalInfo.xml",
                body=mock_xml_responses["info/generalInfo.xml"],
                content_type="text/xml",
            )

            api = IpAPI(mock_config)
            info = await api.info()

            mock_get_mac_address.assert_called_once_with("ip4", "192.168.1.1")
            assert info["mac"] == "00:01:02:04:00:12"


@pytest.mark.asyncio
async def test_info_failed_response(mock_config):
    with aioresponses() as mocked:
        mocked.get("http://192.168.1.1:8080/xml/info/generalInfo.xml", status=500)

        api = IpAPI(mock_config)
        with pytest.raises(ClientError):
            info = await api.info()


@pytest.mark.asyncio
async def test_info_without_mac(mock_config, mock_xml_responses):
    with patch(
        "getmac.getmac.get_by_method", return_value=None
    ) as mock_get_mac_address:
        mock_get_mac_address.return_value = None

        with aioresponses() as mocked:
            mocked.get(
                "http://192.168.1.1:8080/xml/info/generalInfo.xml",
                body=mock_xml_responses["info/generalInfo.xml"],
                content_type="text/xml",
            )

            api = IpAPI(mock_config)
            info = await api.info()

            assert info["mac"] == None


@pytest.mark.asyncio
async def test_get_zones_successfull(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/info/generalInfo.xml",
            body=mock_xml_responses["info/generalInfo.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/zones/zonesStatus128IP.xml",
            body=mock_xml_responses["zones/zonesStatus128IP.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/zones/zonesDescription128IP.xml",
            body=mock_xml_responses["zones/zonesDescription128IP.xml"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)
        zones = await api.get_zones()

        mocked.assert_called
        assert len(zones) == 3
        assert zones[0].description == "Description 1"
        assert zones[0].id == 0
        assert zones[0].bypass == ZoneBypass.OFF
        assert zones[0].status == ZoneStatus.NORMAL
        assert zones[0].enabled == True

        assert zones[1].description == "Description 2"
        assert zones[1].id == 1
        assert zones[1].bypass == ZoneBypass.ON
        assert zones[1].status == ZoneStatus.ALARM
        assert zones[1].enabled == True

        assert zones[2].description is None
        assert zones[2].id == 2
        assert zones[2].bypass == ZoneBypass.OFF
        assert zones[2].status == ZoneStatus.NOT_USED
        assert zones[2].enabled == False


@pytest.mark.asyncio
async def test_get_partitions_successfull(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/info/generalInfo.xml",
            body=mock_xml_responses["info/generalInfo.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/partitions/partitionsStatus128IP.xml",
            body=mock_xml_responses["partitionsStatus.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/partitions/partitionsDescription128IP.xml",
            body=mock_xml_responses["partitionsDescription.xml"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)
        result = await api.get_partitions()

        mocked.assert_called
        assert len(result) == 2
        assert result[0].description == "Description 1"
        assert result[0].id == 0
        assert result[0].status == PartitionStatus.ARMED
        assert result[0].enabled == True

        assert result[1].description is None
        assert result[1].id == 1
        assert result[1].status == PartitionStatus.DISARMED
        assert result[1].enabled == False


@pytest.mark.asyncio
async def test_get_partitions_caches_descriptions(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/info/generalInfo.xml",
            body=mock_xml_responses["info/generalInfo.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/partitions/partitionsStatus128IP.xml",
            body=mock_xml_responses["partitionsStatus.xml"],
            content_type="text/xml",
            repeat=2,
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/partitions/partitionsDescription128IP.xml",
            body=mock_xml_responses["partitionsDescription.xml"],
            content_type="text/xml",
            repeat=False,
        )

        api = IpAPI(mock_config)
        await api.get_partitions()

        mocked.get(
            "http://192.168.1.1:8080/xml/partitions/partitionsDescription128IP.xml",
            status=500,  # We fail the second request to test it is only called once
        )

        await api.get_partitions()
        mocked.assert_called()


@pytest.mark.asyncio
async def test_get_scenarios_successfull(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/info/generalInfo.xml",
            body=mock_xml_responses["info/generalInfo.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/scenarios/scenariosOptions.xml",
            body=mock_xml_responses["scenariosOptions.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/scenarios/scenariosDescription.xml",
            body=mock_xml_responses["scenariosDescription.xml"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)
        result = await api.get_scenarios()

        mocked.assert_called
        assert len(result) == 3
        assert result[0].description == "Turn off"
        assert result[0].id == 0
        assert result[0].enabled == True
        assert result[0].no_pin == True

        assert result[1].description == "Alarm on"
        assert result[1].id == 1
        assert result[1].enabled == True
        assert result[1].no_pin == False

        assert result[2].description == "Scenario"
        assert result[2].id == 2
        assert result[2].enabled == False
        assert result[2].no_pin == False


@pytest.mark.asyncio
async def test_activate_scenario_successfull(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/cmd/cmdOk.xml?cmd=setMacro&redirectPage=/xml/cmd/cmdError.xml&macroId=1",
            body=mock_xml_responses["CommandSuccess"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)
        test_scenario = Scenario(id=1, description="Test", enabled=True, no_pin=True)

        result = await api.activate_scenario(scenario=test_scenario, pin=None)

        mocked.assert_called
        assert result == True


@pytest.mark.asyncio
async def test_activate_scenario_missingPin(mock_config):
    api = IpAPI(mock_config)
    test_scenario = Scenario(id=1, description="Test", enabled=True, no_pin=False)

    with pytest.raises(ValueError):
        await api.activate_scenario(scenario=test_scenario, pin=None)


@pytest.mark.asyncio
async def test_activate_scenario_gets_details_for_id(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/cmd/cmdOk.xml?cmd=setMacro&redirectPage=/xml/cmd/cmdError.xml&macroId=0",
            body=mock_xml_responses["CommandSuccess"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/info/generalInfo.xml",
            body=mock_xml_responses["info/generalInfo.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/scenarios/scenariosOptions.xml",
            body=mock_xml_responses["scenariosOptions.xml"],
            content_type="text/xml",
        )

        mocked.get(
            "http://192.168.1.1:8080/xml/scenarios/scenariosDescription.xml",
            body=mock_xml_responses["scenariosDescription.xml"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)

        result = await api.activate_scenario(scenario=0, pin=None)

        mocked.assert_called
        assert result


@pytest.mark.asyncio
async def test_bypass_zone_for_bypass(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/cmd/cmdOk.xml?cmd=setByPassZone&redirectPage=/xml/cmd/cmdError.xml&pin=123&zoneId=1&zoneValue=1",
            body=mock_xml_responses["CommandSuccess"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)
        test_zone = Zone(
            id=0, description="test", status=ZoneStatus.NORMAL, bypass=ZoneBypass.ON
        )

        result = await api.bypass_zone(zone=test_zone, pin="123", bypass=ZoneBypass.ON)

        mocked.assert_called
        assert result == True


@pytest.mark.asyncio
async def test_bypass_zone_for_unbypass(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/cmd/cmdOk.xml?cmd=setByPassZone&redirectPage=/xml/cmd/cmdError.xml&pin=123&zoneId=1&zoneValue=0",
            body=mock_xml_responses["CommandSuccess"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)
        test_zone = Zone(
            id=0, description="test", status=ZoneStatus.NORMAL, bypass=ZoneBypass.ON
        )

        result = await api.bypass_zone(zone=test_zone, pin="123", bypass=ZoneBypass.OFF)

        mocked.assert_called
        assert result == True


@pytest.mark.asyncio
async def test_bypass_zone_with_id(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/cmd/cmdOk.xml?cmd=setByPassZone&redirectPage=/xml/cmd/cmdError.xml&pin=123&zoneId=1&zoneValue=1",
            body=mock_xml_responses["CommandSuccess"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)

        result = await api.bypass_zone(zone=0, pin="123", bypass=ZoneBypass.ON)

        mocked.assert_called
        assert result == True


@pytest.mark.asyncio
async def test_bypass_zone_failed(mock_config, mock_xml_responses):
    with aioresponses() as mocked:
        mocked.get(
            "http://192.168.1.1:8080/xml/cmd/cmdOk.xml?cmd=setByPassZone&redirectPage=/xml/cmd/cmdError.xml&pin=123&zoneId=1&zoneValue=1",
            body=mock_xml_responses["CommandFailed"],
            content_type="text/xml",
        )

        api = IpAPI(mock_config)

        result = await api.bypass_zone(zone=0, pin="123", bypass=ZoneBypass.ON)

        mocked.assert_called
        assert result == False
