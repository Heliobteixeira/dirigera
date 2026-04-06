import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

import dirigera

mcp = FastMCP("dirigera", instructions="Control IKEA Dirigera Smart Home Hub devices.")


def _get_hub() -> dirigera.Hub:
    token = os.environ.get("DIRIGERA_TOKEN")
    ip_address = os.environ.get("DIRIGERA_IP_ADDRESS")
    if not token or not ip_address:
        raise ValueError(
            "Set DIRIGERA_TOKEN and DIRIGERA_IP_ADDRESS environment variables."
        )
    return dirigera.Hub(token=token, ip_address=ip_address)


def _device_summary(device) -> dict:
    return {
        "id": device.id,
        "name": device.attributes.custom_name,
        "type": device.type,
        "device_type": device.device_type,
        "is_reachable": device.is_reachable,
        "room": device.room.name if device.room else None,
    }


@mcp.tool()
def list_devices() -> str:
    """List all devices registered in the Dirigera hub.
    Returns a JSON array of devices with id, name, type, and room."""
    hub = _get_hub()
    devices = []
    for getter in [
        hub.get_lights,
        hub.get_outlets,
        hub.get_air_purifiers,
        hub.get_blinds,
        hub.get_controllers,
        hub.get_environment_sensors,
        hub.get_motion_sensors,
        hub.get_open_close_sensors,
        hub.get_water_sensors,
    ]:
        try:
            devices.extend(getter())
        except Exception:
            continue
    return json.dumps([_device_summary(d) for d in devices], indent=2)


@mcp.tool()
def get_device(device_id: str) -> str:
    """Get detailed information about a specific device by its ID.

    Args:
        device_id: The unique identifier of the device.
    """
    hub = _get_hub()
    data = hub.get(route=f"/devices/{device_id}")
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def control_light(
    device_id: str,
    on: Optional[bool] = None,
    brightness: Optional[int] = None,
    color_temp: Optional[int] = None,
) -> str:
    """Control a light device. Set any combination of power, brightness, and color temperature.

    Args:
        device_id: The unique identifier of the light.
        on: Turn the light on (true) or off (false).
        brightness: Brightness level between 1 and 100.
        color_temp: Color temperature in mireds.
    """
    hub = _get_hub()
    light = hub.get_light_by_id(device_id)
    actions = []

    if on is not None:
        light.set_light(lamp_on=on)
        actions.append(f"power={'on' if on else 'off'}")

    if brightness is not None:
        light.set_light_level(light_level=brightness)
        actions.append(f"brightness={brightness}")

    if color_temp is not None:
        light.set_color_temperature(color_temp=color_temp)
        actions.append(f"color_temp={color_temp}")

    if not actions:
        return json.dumps(
            {"error": "No action specified. Set on, brightness, or color_temp."}
        )

    return json.dumps(
        {
            "success": True,
            "device_id": device_id,
            "name": light.attributes.custom_name,
            "actions": actions,
        }
    )


@mcp.tool()
def read_sensor(device_id: str) -> str:
    """Read data from a sensor device. Auto-detects the sensor type and returns relevant data.

    Args:
        device_id: The unique identifier of the sensor.
    """
    hub = _get_hub()
    data = hub.get(route=f"/devices/{device_id}")
    device_type = data.get("deviceType", "")

    if device_type == "environmentSensor":
        sensor = hub.get_environment_sensor_by_id(device_id)
        attrs = sensor.attributes
        return json.dumps(
            {
                "type": "environmentSensor",
                "name": attrs.custom_name,
                "temperature": attrs.current_temperature,
                "humidity": attrs.current_r_h,
                "pm25": attrs.current_p_m25,
                "voc_index": attrs.voc_index,
                "battery_percentage": attrs.battery_percentage,
            }
        )

    if device_type == "motionSensor":
        sensor = hub.get_motion_sensor_by_id(device_id)
        attrs = sensor.attributes
        return json.dumps(
            {
                "type": "motionSensor",
                "name": attrs.custom_name,
                "is_detected": attrs.is_detected,
                "is_on": attrs.is_on,
                "light_level": attrs.light_level,
                "battery_percentage": attrs.battery_percentage,
            }
        )

    return json.dumps(
        {"error": f"Unsupported sensor type: {device_type}", "raw": data}, default=str
    )


def main():
    mcp.run(transport="stdio")
