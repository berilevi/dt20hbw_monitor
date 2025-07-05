"""Config flow for DT20HBW Monitor with local IP discovery and port conflict handling."""
import voluptuous as vol
import tinytuya
import logging

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_ID
from homeassistant.core import callback

from .const import DOMAIN, CONF_KEY, CONF_VERSION

_LOGGER = logging.getLogger(__name__)

class DT20HBWMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DT20HBW Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        errors = {}
        if user_input is not None:
            device_id = user_input[CONF_ID]
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            
            device_ip = user_input.get(CONF_HOST)
            
            if not device_ip:
                _LOGGER.info("No IP provided, attempting local discovery for device %s", device_id)
                try:
                    devices = await self.hass.async_add_executor_job(tinytuya.deviceScan, False, 20)
                    _LOGGER.debug("Discovered devices: %s", devices)
                    
                    found_device = devices.get(device_id)
                    if found_device and 'ip' in found_device:
                        device_ip = found_device['ip']
                        _LOGGER.info("Discovered device %s at IP %s", device_id, device_ip)
                    else:
                        errors["base"] = "discovery_failed"
                        _LOGGER.error("Could not discover device %s on the local network.", device_id)
                
                except OSError as e:
                    if e.errno == 98:
                        _LOGGER.error("Tuya discovery port is already in use by another process.")
                        errors["base"] = "discovery_port_in_use"
                    else:
                        _LOGGER.error("An OS error occurred during device discovery: %s", e)
                        errors["base"] = "discovery_failed"
                except Exception as e:
                    _LOGGER.error("An unexpected error occurred during device discovery: %s", e)
                    errors["base"] = "discovery_failed"

            if device_ip:
                final_data = {
                    CONF_ID: device_id,
                    CONF_KEY: user_input[CONF_KEY],
                    CONF_HOST: device_ip,
                    CONF_VERSION: user_input[CONF_VERSION],
                }
                return self.async_create_entry(
                    title=f"DT20HBW Monitor ({device_id})",
                    data=final_data,
                )

        data_schema = vol.Schema({
            vol.Required(CONF_ID): str,
            vol.Required(CONF_KEY): str,
            vol.Optional(CONF_HOST): str,
            vol.Required(CONF_VERSION, default='3.5'): vol.In(['3.1', '3.3', '3.4', '3.5']),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "instructions": (
                    "Enter Device ID and Local Key. Leave 'Host' blank for auto-discovery. "
                    "If discovery fails (e.g., due to other Tuya integrations), find the IP in your "
                    "router and enter it manually."
                )
            }
        )


