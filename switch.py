"""Switch platform for DT20HBW Monitor."""
from homeassistant.components.switch import SwitchEntity
from .entity import DT20HBWMonitorEntity

# DP_ID, Name, Icon
SWITCHES = [
    (102, "Relay Switch", "mdi:electric-switch"),
    (101, "Fast Data Refresh", "mdi:refresh-auto"),
]

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[entry.domain][entry.entry_id]
    coordinator, device = data["coordinator"], data["device"]
    entities = [ DT20HBWMonitorSwitch(coordinator, device, entry.entry_id, *params) for params in SWITCHES ]
    async_add_entities(entities)

class DT20HBWMonitorSwitch(DT20HBWMonitorEntity, SwitchEntity):
    def __init__(self, coordinator, device, entry_id, dp_id, name, icon):
        super().__init__(coordinator, entry_id)
        self._device = device
        self._dp_id = str(dp_id)
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{self._dp_id}"
        self._attr_icon = icon

    @property
    def is_on(self):
        return self.coordinator.data.get(self._dp_id, False) if self.coordinator.data else False

    async def async_turn_on(self, **kwargs):
        await self.hass.async_add_executor_job(self._device.set_value, self._dp_id, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(self._device.set_value, self._dp_id, False)
        await self.coordinator.async_request_refresh()


