import json
from unittest.mock import patch, MagicMock

import pytest

from src.dirigera.mcp_server.server import (
    list_devices,
    get_device,
    control_light,
    read_sensor,
    _load_config,
    CONFIG_PATH,
)
from src.dirigera.hub.abstract_smart_home_hub import FakeDirigeraHub
from src.dirigera.devices.light import dict_to_light
from src.dirigera.devices.environment_sensor import dict_to_environment_sensor
from src.dirigera.devices.motion_sensor import dict_to_motion_sensor


FAKE_LIGHT_DATA = {
    "id": "light-001",
    "type": "light",
    "deviceType": "light",
    "createdAt": "2023-01-07T20:07:19.000Z",
    "isReachable": True,
    "lastSeen": "2023-10-28T04:42:14.000Z",
    "attributes": {
        "customName": "Living Room Light",
        "model": "TRADFRIbulbE27",
        "manufacturer": "IKEA of Sweden",
        "firmwareVersion": "1.0.012",
        "hardwareVersion": "1",
        "isOn": False,
        "lightLevel": 50,
        "colorTemperature": 2700,
        "colorTemperatureMin": 4000,
        "colorTemperatureMax": 2202,
    },
    "capabilities": {
        "canSend": [],
        "canReceive": ["customName", "isOn", "lightLevel", "colorTemperature"],
    },
    "room": {
        "id": "room-001",
        "name": "Living Room",
        "color": "ikea_yellow_no_24",
        "icon": "rooms_living",
    },
    "deviceSet": [],
    "remoteLinks": [],
    "isHidden": False,
}

FAKE_ENV_SENSOR_DATA = {
    "id": "sensor-env-001",
    "type": "sensor",
    "deviceType": "environmentSensor",
    "createdAt": "2023-01-07T20:07:19.000Z",
    "isReachable": True,
    "lastSeen": "2023-10-28T04:42:14.000Z",
    "attributes": {
        "customName": "Bedroom Sensor",
        "model": "VINDSTYRKA",
        "manufacturer": "IKEA of Sweden",
        "firmwareVersion": "1.0.0",
        "hardwareVersion": "1",
        "currentTemperature": 22.5,
        "currentRH": 45,
        "currentPM25": 12,
        "vocIndex": 150,
        "batteryPercentage": 80,
    },
    "capabilities": {"canSend": [], "canReceive": ["customName"]},
    "room": {
        "id": "room-002",
        "name": "Bedroom",
        "color": "ikea_yellow_no_24",
        "icon": "rooms_bed",
    },
    "deviceSet": [],
    "remoteLinks": [],
    "isHidden": False,
}

FAKE_MOTION_SENSOR_DATA = {
    "id": "sensor-motion-001",
    "type": "sensor",
    "deviceType": "motionSensor",
    "createdAt": "2023-01-07T20:07:19.000Z",
    "isReachable": True,
    "lastSeen": "2023-10-28T04:42:14.000Z",
    "attributes": {
        "customName": "Hallway Motion",
        "model": "TRADFRI",
        "manufacturer": "IKEA of Sweden",
        "firmwareVersion": "1.0.0",
        "hardwareVersion": "1",
        "isOn": True,
        "isDetected": False,
        "lightLevel": 120.5,
        "batteryPercentage": 95,
    },
    "capabilities": {"canSend": [], "canReceive": ["customName"]},
    "room": {
        "id": "room-003",
        "name": "Hallway",
        "color": "ikea_yellow_no_24",
        "icon": "rooms_hallway",
    },
    "deviceSet": [],
    "remoteLinks": [],
    "isHidden": False,
}


def _make_fake_hub():
    fake = FakeDirigeraHub()
    return fake


@patch("src.dirigera.mcp_server.server._get_hub")
def test_list_devices(mock_get_hub):
    fake = _make_fake_hub()
    light = dict_to_light(FAKE_LIGHT_DATA, fake)

    mock_hub = MagicMock()
    mock_hub.get_lights.return_value = [light]
    mock_hub.get_outlets.return_value = []
    mock_hub.get_air_purifiers.return_value = []
    mock_hub.get_blinds.return_value = []
    mock_hub.get_controllers.return_value = []
    mock_hub.get_environment_sensors.return_value = []
    mock_hub.get_motion_sensors.return_value = []
    mock_hub.get_open_close_sensors.return_value = []
    mock_hub.get_water_sensors.return_value = []
    mock_get_hub.return_value = mock_hub

    result = json.loads(list_devices())
    assert len(result) == 1
    assert result[0]["id"] == "light-001"
    assert result[0]["name"] == "Living Room Light"
    assert result[0]["type"] == "light"
    assert result[0]["room"] == "Living Room"
    assert result[0]["is_reachable"] is True


@patch("src.dirigera.mcp_server.server._get_hub")
def test_get_device(mock_get_hub):
    mock_hub = MagicMock()
    mock_hub.get.return_value = FAKE_LIGHT_DATA
    mock_get_hub.return_value = mock_hub

    result = json.loads(get_device("light-001"))
    assert result["id"] == "light-001"
    assert result["attributes"]["customName"] == "Living Room Light"


@patch("src.dirigera.mcp_server.server._get_hub")
def test_control_light_on(mock_get_hub):
    fake = _make_fake_hub()
    light = dict_to_light(FAKE_LIGHT_DATA, fake)

    mock_hub = MagicMock()
    mock_hub.get_light_by_id.return_value = light
    mock_get_hub.return_value = mock_hub

    result = json.loads(control_light("light-001", on=True))
    assert result["success"] is True
    assert "power=on" in result["actions"]
    action = fake.patch_actions.pop()
    assert action["data"] == [{"attributes": {"isOn": True}}]


@patch("src.dirigera.mcp_server.server._get_hub")
def test_control_light_brightness(mock_get_hub):
    fake = _make_fake_hub()
    light = dict_to_light(FAKE_LIGHT_DATA, fake)

    mock_hub = MagicMock()
    mock_hub.get_light_by_id.return_value = light
    mock_get_hub.return_value = mock_hub

    result = json.loads(control_light("light-001", brightness=75))
    assert result["success"] is True
    assert "brightness=75" in result["actions"]
    action = fake.patch_actions.pop()
    assert action["data"] == [{"attributes": {"lightLevel": 75}}]


@patch("src.dirigera.mcp_server.server._get_hub")
def test_control_light_no_action(mock_get_hub):
    fake = _make_fake_hub()
    light = dict_to_light(FAKE_LIGHT_DATA, fake)

    mock_hub = MagicMock()
    mock_hub.get_light_by_id.return_value = light
    mock_get_hub.return_value = mock_hub

    result = json.loads(control_light("light-001"))
    assert "error" in result


@patch("src.dirigera.mcp_server.server._get_hub")
def test_read_environment_sensor(mock_get_hub):
    fake = _make_fake_hub()
    sensor = dict_to_environment_sensor(FAKE_ENV_SENSOR_DATA, fake)

    mock_hub = MagicMock()
    mock_hub.get.return_value = FAKE_ENV_SENSOR_DATA
    mock_hub.get_environment_sensor_by_id.return_value = sensor
    mock_get_hub.return_value = mock_hub

    result = json.loads(read_sensor("sensor-env-001"))
    assert result["type"] == "environmentSensor"
    assert result["temperature"] == 22.5
    assert result["humidity"] == 45
    assert result["pm25"] == 12
    assert result["voc_index"] == 150


@patch("src.dirigera.mcp_server.server._get_hub")
def test_read_motion_sensor(mock_get_hub):
    fake = _make_fake_hub()
    sensor = dict_to_motion_sensor(FAKE_MOTION_SENSOR_DATA, fake)

    mock_hub = MagicMock()
    mock_hub.get.return_value = FAKE_MOTION_SENSOR_DATA
    mock_hub.get_motion_sensor_by_id.return_value = sensor
    mock_get_hub.return_value = mock_hub

    result = json.loads(read_sensor("sensor-motion-001"))
    assert result["type"] == "motionSensor"
    assert result["is_detected"] is False
    assert result["is_on"] is True
    assert result["light_level"] == 120.5
    assert result["battery_percentage"] == 95


def test_load_config_missing_file():
    with patch("src.dirigera.mcp_server.server.CONFIG_PATH") as mock_path:
        mock_path.exists.return_value = False
        with pytest.raises(FileNotFoundError):
            _load_config()
