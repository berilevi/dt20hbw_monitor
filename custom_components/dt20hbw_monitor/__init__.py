"""The DT20HBW Monitor integration."""
from datetime import timedelta
import logging
import tinytuya

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_KEY, CONF_VERSION

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.BUTTON,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    device = tinytuya.Device(
        entry.data[CONF_ID],
        entry.data[CONF_HOST],
        entry.data[CONF_KEY],
    )
    device.set_version(float(entry.data[CONF_VERSION]))
    device.set_socketTimeout(15)  # Increased from 5 to 15 seconds for better reliability

    # Validate device connection before setting up coordinator
    _LOGGER.info(
        "Testing connection to device %s at %s (version %s)",
        entry.data[CONF_ID],
        entry.data[CONF_HOST],
        entry.data[CONF_VERSION]
    )

    # Attempt initial connection test
    test_status = await hass.async_add_executor_job(device.status)
    if test_status and isinstance(test_status, dict) and 'Error' in test_status:
        error_msg = test_status.get('Error', 'Unknown error')
        error_code = test_status.get('Err', 'N/A')

        _LOGGER.error(
            "Failed to connect to device %s at %s: Error %s - %s",
            entry.data[CONF_ID],
            entry.data[CONF_HOST],
            error_code,
            error_msg
        )

        # Provide user-friendly error message
        if error_code == '905':
            raise ConfigEntryNotReady(
                f"Device unreachable at {entry.data[CONF_HOST]}. "
                f"Please verify the device is powered on and connected to your network."
            )
        elif error_code == '901':
            raise ConfigEntryNotReady(
                f"Cannot connect to device at {entry.data[CONF_HOST]}. "
                f"Please verify the IP address and that the device is on the same network."
            )

        elif error_code == '914':
            raise UpdateFailed(
                f"Authentication failed - incorrect device key or protocol version. "
                f"Error {error_code}: {error_msg}"
            )
        else:
            raise ConfigEntryNotReady(
                f"Device connection failed: Error {error_code} - {error_msg}"
            )

    _LOGGER.info(
        "Successfully connected to device %s at %s",
        entry.data[CONF_ID],
        entry.data[CONF_HOST]
    )

    async def async_update_data():
        try:
            status = await hass.async_add_executor_job(device.status)

            # Check for tinytuya error responses first
            if status and isinstance(status, dict) and 'Error' in status:
                error_msg = status.get('Error', 'Unknown error')
                error_code = status.get('Err', 'N/A')

                # Provide specific error messages based on error code
                if error_code == '905':
                    raise UpdateFailed(
                        f"Device unreachable at {entry.data[CONF_HOST]}. "
                        f"Check that device is powered on and connected to network. "
                        f"Error {error_code}: {error_msg}"
                    )
                elif error_code == '901':
                    raise UpdateFailed(
                        f"Unable to connect to device at {entry.data[CONF_HOST]}. "
                        f"Verify IP address and network connectivity. "
                        f"Error {error_code}: {error_msg}"
                    )
                else:
                    raise UpdateFailed(
                        f"Device error {error_code}: {error_msg}"
                    )

            # Now check for valid data
            if status and isinstance(status, dict) and 'dps' in status:
                return status['dps']

            # Log unexpected response for debugging
            _LOGGER.warning(
                "Unexpected response from device %s: %s",
                entry.data[CONF_ID],
                status
            )
            raise UpdateFailed(f"Invalid response from device (no 'dps' data): {status}")

        except UpdateFailed:
            # Re-raise UpdateFailed exceptions without wrapping
            raise
        except Exception as err:
            _LOGGER.exception(
                "Unexpected error communicating with device %s at %s",
                entry.data[CONF_ID],
                entry.data[CONF_HOST]
            )
            raise UpdateFailed(f"Error communicating with device: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.data[CONF_ID]}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=60),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "device": device}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


