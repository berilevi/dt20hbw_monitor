"""Config flow for DT20HBW Monitor."""

from __future__ import annotations

import logging
from typing import Any

import tinytuya
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_ID

from .const import DOMAIN, CONF_KEY, CONF_VERSION
from .tuya_device import (
    SUPPORTED_PROTOCOL_VERSIONS,
    TuyaAuthError,
    TuyaConnectionError,
    TuyaUnexpectedResponseError,
    async_probe_device,
    normalize_device_config,
)

_LOGGER = logging.getLogger(__name__)


class DT20HBWMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for DT20HBW Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial setup flow."""

        return await self._async_handle_device_form(step_id="user", user_input=user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ):
        """Allow the user to update host, key, or protocol version."""

        return await self._async_handle_device_form(
            step_id="reconfigure",
            user_input=user_input,
            entry=self._get_reconfigure_entry(),
            allow_existing_key=True,
        )

    async def async_step_reauth(self, _entry_data: dict[str, Any]):
        """Start reauthentication for an existing entry."""

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Handle key updates after an authentication failure."""

        return await self._async_handle_device_form(
            step_id="reauth_confirm",
            user_input=user_input,
            entry=self._get_reauth_entry(),
        )

    async def _async_handle_device_form(
        self,
        *,
        step_id: str,
        user_input: dict[str, Any] | None,
        entry: ConfigEntry | None = None,
        allow_existing_key: bool = False,
    ):
        """Render and process a device configuration form."""

        errors: dict[str, str] = {}
        defaults = normalize_device_config(entry.data) if entry else {}

        if user_input is not None:
            data = self._normalize_user_input(
                user_input,
                defaults=defaults,
                allow_existing_key=allow_existing_key,
            )

            device_id = defaults.get(CONF_ID, data[CONF_ID])
            await self.async_set_unique_id(device_id)
            if entry is None:
                self._abort_if_unique_id_configured()
            else:
                self._abort_if_unique_id_mismatch()

            if not data[CONF_HOST]:
                data[CONF_HOST] = await self._async_discover_device_ip(device_id, errors)

            if data[CONF_HOST]:
                try:
                    probe = await async_probe_device(
                        self.hass,
                        device_id,
                        data[CONF_HOST],
                        data[CONF_KEY],
                        data[CONF_VERSION],
                    )
                except TuyaAuthError as err:
                    _LOGGER.warning(
                        "Authentication failed for device %s after trying protocol versions %s",
                        device_id,
                        ", ".join(err.tried_versions),
                    )
                    errors["base"] = "invalid_auth"
                except TuyaConnectionError as err:
                    _LOGGER.warning(
                        "Device %s at %s returned TinyTuya error %s: %s",
                        device_id,
                        data[CONF_HOST],
                        err.error_code,
                        err.message,
                    )
                    errors["base"] = "cannot_connect"
                except TuyaUnexpectedResponseError:
                    _LOGGER.warning(
                        "Device %s returned an unexpected response during validation",
                        device_id,
                    )
                    errors["base"] = "invalid_response"
                except Exception:
                    _LOGGER.exception("Unexpected error validating device %s", device_id)
                    errors["base"] = "unknown"
                else:
                    final_data = {
                        CONF_ID: device_id,
                        CONF_KEY: data[CONF_KEY],
                        CONF_HOST: data[CONF_HOST],
                        CONF_VERSION: probe.version,
                    }

                    if entry is None:
                        return self.async_create_entry(
                            title=f"DT20HBW Monitor ({device_id})",
                            data=final_data,
                        )

                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates=final_data,
                    )

        return self.async_show_form(
            step_id=step_id,
            data_schema=self._build_schema(
                defaults,
                include_device_id=entry is None,
                allow_existing_key=allow_existing_key,
            ),
            errors=errors,
        )

    def _build_schema(
        self,
        defaults: dict[str, str],
        *,
        include_device_id: bool,
        allow_existing_key: bool,
    ) -> vol.Schema:
        """Build the schema for the active config flow step."""

        schema: dict[Any, Any] = {}

        if include_device_id:
            schema[
                vol.Required(
                    CONF_ID,
                    default=defaults.get(CONF_ID, vol.UNDEFINED),
                )
            ] = str

        key_marker = vol.Optional if allow_existing_key else vol.Required
        key_default = (
            defaults.get(CONF_KEY, vol.UNDEFINED)
            if include_device_id and not allow_existing_key
            else vol.UNDEFINED
        )
        schema[
            key_marker(
                CONF_KEY,
                default=key_default,
            )
        ] = str
        schema[
            vol.Optional(
                CONF_HOST,
                default=defaults.get(CONF_HOST, ""),
            )
        ] = str
        schema[
            vol.Required(
                CONF_VERSION,
                default=defaults.get(CONF_VERSION, SUPPORTED_PROTOCOL_VERSIONS[-1]),
            )
        ] = vol.In(SUPPORTED_PROTOCOL_VERSIONS)

        return vol.Schema(schema)

    def _normalize_user_input(
        self,
        user_input: dict[str, Any],
        *,
        defaults: dict[str, str],
        allow_existing_key: bool,
    ) -> dict[str, str]:
        """Normalize and merge user input with the existing entry when needed."""

        normalized = normalize_device_config(
            {
                CONF_ID: user_input.get(CONF_ID, defaults.get(CONF_ID, "")),
                CONF_KEY: user_input.get(CONF_KEY, ""),
                CONF_HOST: user_input.get(CONF_HOST, ""),
                CONF_VERSION: user_input.get(
                    CONF_VERSION,
                    defaults.get(CONF_VERSION, SUPPORTED_PROTOCOL_VERSIONS[-1]),
                ),
            }
        )

        if allow_existing_key and not normalized[CONF_KEY]:
            normalized[CONF_KEY] = defaults[CONF_KEY]

        return normalized

    async def _async_discover_device_ip(
        self,
        device_id: str,
        errors: dict[str, str],
    ) -> str:
        """Discover the device IP using TinyTuya on the local network."""

        _LOGGER.info("No IP provided, attempting local discovery for device %s", device_id)

        try:
            devices = await self.hass.async_add_executor_job(
                tinytuya.deviceScan,
                False,
                20,
            )
            _LOGGER.debug("Discovered devices: %s", devices)

            found_device = devices.get(device_id)
            if found_device and "ip" in found_device:
                device_ip = str(found_device["ip"]).strip()
                _LOGGER.info("Discovered device %s at IP %s", device_id, device_ip)
                return device_ip

            errors["base"] = "discovery_failed"
            _LOGGER.warning("Could not discover device %s on the local network", device_id)
            return ""

        except OSError as err:
            if err.errno == 98:
                _LOGGER.warning("Tuya discovery port is already in use")
                errors["base"] = "discovery_port_in_use"
            else:
                _LOGGER.warning("OS error during device discovery for %s: %s", device_id, err)
                errors["base"] = "discovery_failed"
            return ""
        except Exception:
            _LOGGER.exception("Unexpected error during device discovery for %s", device_id)
            errors["base"] = "discovery_failed"
            return ""
