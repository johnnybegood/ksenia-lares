from unittest.mock import patch
from aiohttp import ClientConnectorError, ClientError
import pytest
from aioresponses import aioresponses
from ksenia_lares import IpAPI 
from ksenia_lares.types import AlarmInfo, Zone, ZoneStatus

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
                <status>ACTIVE</status>
                <bypass>FALSE</bypass>
            </zone>
            <zone>
                <status>INACTIVE</status>
                <bypass>TRUE</bypass>
            </zone>
        </zonesStatus>
        """,
        "zones/zonesDescription128IP.xml": """
        <zonesDescription>
            <zone>Description 1</zone>
            <zone>Description 2</zone>
        </zonesDescription>
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
    with patch("getmac.getmac.get_by_method", return_value="00:01:02:04:00:12") as mock_get_mac_address:
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
        mocked.get(
            "http://192.168.1.1:8080/xml/info/generalInfo.xml",
            status=500
        )

        api = IpAPI(mock_config)
        with pytest.raises(ClientError):
            info = await api.info()

@pytest.mark.asyncio
async def test_info_without_mac(mock_config, mock_xml_responses):
   with patch("getmac.getmac.get_by_method", return_value=None) as mock_get_mac_address:
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