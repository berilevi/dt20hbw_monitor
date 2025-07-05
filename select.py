"""Select platform for DT20HBW Monitor."""
from homeassistant.components.select import SelectEntity
from .entity import DT20HBWMonitorEntity

SELECTS = [
    (107, "Language", ["chinese", "english"]),
    (136, "Diverter Size", ["30A", "100A", "200A", "300A", "400A", "500A", "600A", "1000A"]),
    (118, "Display Style", ["front", "back", "display_off"]),
]

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[entry.domain][entry.entry_id]
    coordinator, device = data["coordinator"], data["device"]
    entities = [ DT20HBWMonitorSelect(coordinator, device, entry.entry_id, *params) for params in SELECTS ]
    async_add_entities(entities)

class DT20HBWMonitorSelect(DT20HBWMonitorEntity, SelectEntity):
    def __init__(self, coordinator, device, entry_id, dp_id, name, options):
        super().__init__(coordinator, entry_id)
        self._device = device
        self._dp_id = str(dp_id)
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{self._dp_id}"
        self._attr_options = options

    @property
    def current_option(self):
        return self.coordinator.data.get(self._dp_id) if self.coordinator.data else None

    async def async_select_option(self, option: str) -> None:
        await self.hass.async_add_executor_job(self._device.set_value, self._dp_id, option)
        await self.coordinator.async_request_refresh()


