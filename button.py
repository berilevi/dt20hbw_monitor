"""Button platform for DT20HBW Monitor."""
from homeassistant.components.button import ButtonEntity
from .entity import DT20HBWMonitorEntity

BUTTONS = [
    (113, "Data Reset", "mdi:database-refresh"),
    (114, "WiFi Reset", "mdi:wifi-refresh"),
    (115, "Factory Reset", "mdi:factory"),
    (116, "Exit Menu", "mdi:exit-run"),
]

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[entry.domain][entry.entry_id]
    coordinator, device = data["coordinator"], data["device"]
    entities = [ DT20HBWMonitorButton(coordinator, device, entry.entry_id, *params) for params in BUTTONS ]
    async_add_entities(entities)

class DT20HBWMonitorButton(DT20HBWMonitorEntity, ButtonEntity):
    def __init__(self, coordinator, device, entry_id, dp_id, name, icon):
        super().__init__(coordinator, entry_id)
        self._device = device
        self._dp_id = str(dp_id)
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{self._dp_id}"
        self._attr_icon = icon

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(self._device.set_value, self._dp_id, True)
