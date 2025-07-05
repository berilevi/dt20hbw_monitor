# --- FILE: custom_components/dt20hbw_monitor/sensor.py ---
"""Sensor platform for DT20HBW Monitor."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from .entity import DT20HBWMonitorEntity

# DP_ID, Name, Unit, Device Class, Scale Factor, State Class, Icon
SENSORS = [
    (20, "Voltage", "V", SensorDeviceClass.VOLTAGE, 0.01, SensorStateClass.MEASUREMENT, None),
    (18, "Current", "A", SensorDeviceClass.CURRENT, 0.001, SensorStateClass.MEASUREMENT, None),
    (19, "Power", "W", SensorDeviceClass.POWER, 0.01, SensorStateClass.MEASUREMENT, None),
    (103, "Battery", "%", SensorDeviceClass.BATTERY, 0.1, SensorStateClass.MEASUREMENT, None),
    (122, "NTC Temperature", "°C", SensorDeviceClass.TEMPERATURE, 0.1, SensorStateClass.MEASUREMENT, None),
    (123, "Total Energy", "kWh", SensorDeviceClass.ENERGY, 0.001, SensorStateClass.TOTAL_INCREASING, None),
    (133, "Total Capacity", "Ah", None, 0.001, SensorStateClass.TOTAL_INCREASING, "mdi:battery-plus-variant"),
    (135, "CPU Temperature", "°C", SensorDeviceClass.TEMPERATURE, 1, SensorStateClass.MEASUREMENT, None),
    (132, "Alarm Status", None, None, 1, None, "mdi:alert-outline"),
    (134, "Resistance", "Ω", None, 0.01, SensorStateClass.MEASUREMENT, "mdi:omega"),
    (111, "Discharge Current", "A", SensorDeviceClass.CURRENT, 0.001, SensorStateClass.MEASUREMENT, None),
    (112, "Discharge Power", "W", SensorDeviceClass.POWER, 0.001, SensorStateClass.MEASUREMENT, None),
]

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor entities."""
    data = hass.data[entry.domain][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [ DT20HBWMonitorSensor(coordinator, entry.entry_id, *params) for params in SENSORS ]
    async_add_entities(entities)

class DT20HBWMonitorSensor(DT20HBWMonitorEntity, SensorEntity):
    """Representation of a Sensor."""
    def __init__(self, coordinator, entry_id, dp_id, name, unit, device_class, scale, state_class, icon):
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id)
        self._dp_id = str(dp_id)
        self._scale = scale
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{self._dp_id}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and (value := self.coordinator.data.get(self._dp_id)) is not None:
            # For 'Alarm Status', we just want the string value, not a number
            if self._dp_id == '132':
                return value
            return value * self._scale
        return None
