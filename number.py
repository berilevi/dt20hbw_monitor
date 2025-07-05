"""Number platform for DT20HBW Monitor."""
from homeassistant.components.number import NumberEntity, NumberDeviceClass
from .entity import DT20HBWMonitorEntity

# DP_ID, Name, Min, Max, Step, Unit, Device Class, Scale Factor
NUMBERS = [
    (104, "Over Voltage Protection", 0, 420.00, 0.01, "V", NumberDeviceClass.VOLTAGE, 0.01),
    (119, "Low Voltage Protection", 0, 420.00, 0.01, "V", NumberDeviceClass.VOLTAGE, 0.01),
    (106, "Over Power Protection", 1, 252000, 1, "W", NumberDeviceClass.POWER, 1),
    (105, "Over Temperature Protection", 1.0, 150.0, 0.1, "°C", NumberDeviceClass.TEMPERATURE, 0.1),
    (110, "Standby Time", 3, 99, 1, "s", None, 1),
    (117, "100% Voltage", 0, 450.00, 0.01, "V", NumberDeviceClass.VOLTAGE, 0.01),
    (120, "0% Voltage", 0, 450.00, 0.01, "V", NumberDeviceClass.VOLTAGE, 0.01),
    (108, "Screen Brightness", 1, 9, 1, None, None, 1),
    (109, "Standby Brightness", 0, 9, 1, None, None, 1),
    (121, "Current Threshold", 2, 99, 1, "mA", NumberDeviceClass.CURRENT, 1),
    (125, "Reporting Interval", 1, 90, 1, "s", None, 1),
]

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[entry.domain][entry.entry_id]
    coordinator, device = data["coordinator"], data["device"]
    entities = [ DT20HBWMonitorNumber(coordinator, device, entry.entry_id, *params) for params in NUMBERS ]
    async_add_entities(entities)

class DT20HBWMonitorNumber(DT20HBWMonitorEntity, NumberEntity):
    def __init__(self, coordinator, device, entry_id, dp_id, name, min_val, max_val, step, unit, dev_class, scale):
        super().__init__(coordinator, entry_id)
        self._device = device
        self._dp_id = str(dp_id)
        self._scale = scale
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{self._dp_id}"
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = dev_class

    @property
    def native_value(self):
        if self.coordinator.data and (value := self.coordinator.data.get(self._dp_id)) is not None:
            return value * self._scale if self._scale != 1 else value
        return None

    async def async_set_native_value(self, value: float) -> None:
        scaled_value = int(value / self._scale) if self._scale != 1 else int(value)
        await self.hass.async_add_executor_job(self._device.set_value, self._dp_id, scaled_value)
        await self.coordinator.async_request_refresh()


