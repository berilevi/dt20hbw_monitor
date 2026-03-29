"""The DT20HBW Monitor integration."""
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_KEY, CONF_VERSION
from .tuya_device import (
    TuyaAuthError,
    TuyaConnectionError,
    TuyaUnexpectedResponseError,
    async_probe_device,
    get_tuya_error,
    has_dps_payload,
    normalize_device_config,
)

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
    config = normalize_device_config(entry.data)

    _LOGGER.info(
        "Testing connection to device %s at %s (preferred version %s)",
        config[CONF_ID],
        config[CONF_HOST],
        config[CONF_VERSION],
    )

    try:
        probe = await async_probe_device(
            hass,
            config[CONF_ID],
            config[CONF_HOST],
            config[CONF_KEY],
            config[CONF_VERSION],
        )
    except TuyaConnectionError as err:
        if err.error_code == "905":
            raise ConfigEntryNotReady(
                f"Device unreachable at {config[CONF_HOST]}. "
                f"Please verify the device is powered on and connected to your network."
            ) from err
        if err.error_code == "901":
            raise ConfigEntryNotReady(
                f"Cannot connect to device at {config[CONF_HOST]}. "
                f"Please verify the IP address and that the device is on the same network."
            ) from err
        raise ConfigEntryNotReady(
            f"Device connection failed: Error {err.error_code} - {err.message}"
        ) from err
    except TuyaAuthError as err:
        raise ConfigEntryAuthFailed(
            "Authentication failed. Reconfigure the entry with the current local key."
        ) from err
    except TuyaUnexpectedResponseError as err:
        raise ConfigEntryNotReady(
            f"Device returned an unexpected response during setup: {err.response}"
        ) from err

    device = probe.device
    initial_dps = probe.dps

    updated_data = {
        **entry.data,
        CONF_ID: config[CONF_ID],
        CONF_HOST: config[CONF_HOST],
        CONF_KEY: config[CONF_KEY],
        CONF_VERSION: probe.version,
    }
    if updated_data != entry.data:
        hass.config_entries.async_update_entry(entry, data=updated_data)

    _LOGGER.info(
        "Successfully connected to device %s at %s using protocol version %s",
        config[CONF_ID],
        config[CONF_HOST],
        probe.version,
    )

    async def async_update_data():
        nonlocal initial_dps

        try:
            if initial_dps is not None:
                dps = initial_dps
                initial_dps = None
                return dps

            status = await hass.async_add_executor_job(device.status)

            error = get_tuya_error(status)
            if error is not None:
                error_code, error_msg = error

                if error_code == "905":
                    raise UpdateFailed(
                        f"Device unreachable at {config[CONF_HOST]}. "
                        f"Check that device is powered on and connected to network. "
                        f"Error {error_code}: {error_msg}"
                    )
                if error_code == "901":
                    raise UpdateFailed(
                        f"Unable to connect to device at {config[CONF_HOST]}. "
                        f"Verify IP address and network connectivity. "
                        f"Error {error_code}: {error_msg}"
                    )
                if error_code == "914":
                    raise ConfigEntryAuthFailed(
                        "Authentication failed. Reconfigure the entry with the current local key."
                    )

                raise UpdateFailed(
                    f"Device error {error_code}: {error_msg}"
                )

            if has_dps_payload(status):
                return status["dps"]

            _LOGGER.warning(
                "Unexpected response from device %s: %s",
                config[CONF_ID],
                status,
            )
            raise UpdateFailed(f"Invalid response from device (no 'dps' data): {status}")

        except ConfigEntryAuthFailed:
            raise
        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.exception(
                "Unexpected error communicating with device %s at %s",
                config[CONF_ID],
                config[CONF_HOST],
            )
            raise UpdateFailed(f"Error communicating with device: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{config[CONF_ID]}",
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

