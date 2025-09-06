"""Button platform for DT20HBW Monitor."""
from homeassistant.components.button import ButtonEntity
from .entity import DT20HBWMonitorEntity

# DP_ID, Name, Icon, Payload to send on press
BUTTONS = [
    (132, "Reset Alarm", "mdi:bell-cancel-outline", "off"),
    (113, "Data Reset", "mdi:database-refresh", True),
    (114, "WiFi Reset", "mdi:wifi-refresh", True),
    (115, "Factory Reset", "mdi:factory", True),
    (116, "Exit Menu", "mdi:exit-run", True),
]

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the button entities."""
    data = hass.data[entry.domain][entry.entry_id]
    coordinator, device = data["coordinator"], data["device"]
    
    entities = [ 
        DT20HBWMonitorButton(coordinator, device, entry.entry_id, *params) 
        for params in BUTTONS 
    ]
    async_add_entities(entities)

class DT20HBWMonitorButton(DT20HBWMonitorEntity, ButtonEntity):
    """Representation of a Button entity."""
    
    def __init__(self, coordinator, device, entry_id, dp_id, name, icon, payload):
        """Initialize the button."""
        super().__init__(coordinator, entry_id)
        self._device = device
        self._dp_id = str(dp_id)
        self._payload = payload  # Store the specific payload for this button
        
        # Setting static properties as attributes
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{self._dp_id}_action" # Added _action to avoid conflict with sensor
        self._attr_icon = icon

    async def async_press(self) -> None:
        """Handle the button press by sending the configured payload."""
        await self.hass.async_add_executor_job(
            self._device.set_value, self._dp_id, self._payload
        )
        # We also request a refresh to see the alarm status update immediately
        await self.coordinator.async_request_refresh()
