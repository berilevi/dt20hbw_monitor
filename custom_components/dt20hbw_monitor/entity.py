"""Base entity for DT20HBW Monitor."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

class DT20HBWMonitorEntity(CoordinatorEntity):
    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "DT20HBW Monitor",
            "manufacturer": "Tuya",
        }


