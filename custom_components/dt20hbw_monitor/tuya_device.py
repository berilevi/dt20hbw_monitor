"""Helpers for connecting to DT20HBW Tuya devices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import tinytuya

from homeassistant.const import CONF_HOST, CONF_ID
from homeassistant.core import HomeAssistant

from .const import CONF_KEY, CONF_VERSION

SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = ("3.1", "3.3", "3.4", "3.5")
SOCKET_TIMEOUT = 15


@dataclass(slots=True)
class DeviceProbeResult:
    """Successful device probe details."""

    device: Any
    dps: dict[str, Any]
    version: str


class TuyaConnectionError(Exception):
    """Raised when the device returns a recoverable connection error."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class TuyaAuthError(TuyaConnectionError):
    """Raised when authentication fails for all supported protocol versions."""

    def __init__(
        self,
        message: str,
        tried_versions: tuple[str, ...],
        error_code: str = "914",
    ) -> None:
        super().__init__(error_code, message)
        self.tried_versions = tried_versions


class TuyaUnexpectedResponseError(Exception):
    """Raised when TinyTuya returns an unexpected payload."""

    def __init__(self, response: Any) -> None:
        super().__init__(f"Unexpected response: {response}")
        self.response = response


def normalize_device_config(data: Mapping[str, Any]) -> dict[str, str]:
    """Normalize stored or user-provided device configuration values."""

    return {
        CONF_ID: str(data[CONF_ID]).strip(),
        CONF_KEY: str(data.get(CONF_KEY, "")).strip(),
        CONF_HOST: str(data.get(CONF_HOST, "")).strip(),
        CONF_VERSION: str(data.get(CONF_VERSION, SUPPORTED_PROTOCOL_VERSIONS[-1])).strip(),
    }


def get_tuya_error(status: Any) -> tuple[str, str] | None:
    """Return TinyTuya error details if the response is an error payload."""

    if not isinstance(status, dict) or "Error" not in status:
        return None

    return str(status.get("Err", "N/A")), str(status.get("Error", "Unknown error"))


def has_dps_payload(status: Any) -> bool:
    """Check whether the TinyTuya response contains a DPS payload."""

    return isinstance(status, dict) and isinstance(status.get("dps"), dict)


def build_device(
    device_id: str,
    host: str,
    local_key: str,
    version: str,
):
    """Create a TinyTuya device with the integration defaults applied."""

    device = tinytuya.Device(device_id, host, local_key)
    device.set_version(float(version))
    device.set_socketTimeout(SOCKET_TIMEOUT)
    return device


async def async_probe_device(
    hass: HomeAssistant,
    device_id: str,
    host: str,
    local_key: str,
    preferred_version: str,
    *,
    fallback_versions: bool = True,
) -> DeviceProbeResult:
    """Probe a device and auto-detect the correct protocol version when needed."""

    versions_to_try = [preferred_version]
    if fallback_versions:
        versions_to_try.extend(
            version
            for version in SUPPORTED_PROTOCOL_VERSIONS
            if version != preferred_version
        )

    auth_failures: list[str] = []

    for version in versions_to_try:
        device = build_device(device_id, host, local_key, version)
        status = await hass.async_add_executor_job(device.status)

        if has_dps_payload(status):
            return DeviceProbeResult(device=device, dps=status["dps"], version=version)

        error = get_tuya_error(status)
        if error is None:
            raise TuyaUnexpectedResponseError(status)

        error_code, error_message = error
        if error_code == "914":
            auth_failures.append(version)
            continue

        raise TuyaConnectionError(error_code, error_message)

    raise TuyaAuthError(
        "Authentication failed. Check the local key or unsupported protocol version.",
        tuple(auth_failures or versions_to_try),
    )
