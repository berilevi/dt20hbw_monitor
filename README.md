# DT20HBW Monitor Integration for Home Assistant

This is a custom Home Assistant integration for the DT20HBW Tuya-based Smart Battery Monitor/Coulometer.
It provides complete local control over the device, communicating directly with it on your network without depending on the Tuya cloud (after the initial setup to get the device credentials).

## Features
Purely Local Control: Uses the tinytuya library to communicate directly with your device. No cloud dependency for operation.
Local IP Auto-Discovery: Automatically finds your device on the local network, minimizing configuration. A manual IP fallback is included for complex network setups.
Rich Sensor Data: Creates sensors for Voltage, Current, Power, Battery Percentage, Temperature, Total Energy (kWh), Total Capacity (Ah), and more.
Full Configuration: Provides number and select entities to configure device settings like Over/Under Voltage Protection, Over Power/Temperature Protection, Screen Brightness, and Diverter Size directly from Home Assistant.
Relay Control: A switch entity to turn the device's main relay on and off.
Action Buttons: button entities to trigger actions like resetting data or performing a factory reset.
## Prerequisites
A working Home Assistant instance.
Your DT20HBW device must be connected to your local Wi-Fi network.
You must know your device's Device ID and Local Key.
How to get the Device ID and Local Key
The easiest way to get these credentials is by using the tuya-cli wizard.
Install tuya-cli: pip install tuya-cli
Run the wizard: tuya-cli wizard
Follow the on-screen prompts. It will ask for your Tuya IoT Platform credentials and then list all your devices with their IDs and Local Keys.
Save the id and key for your DT20HBW device.
## Installation
This integration is best installed via the Home Assistant Community Store (HACS).
Ensure HACS is installed.
In Home Assistant, go to HACS > Integrations.
Click the three-dots menu in the top right and select "Custom repositories".
In the dialog box, enter the following:
Repository: https://github.com/berilevi/dt20hbw_monitor
Category: Integration
Click Add.
The "DT20HBW Monitor" integration will now appear in your HACS list. Click on it and then click Download.
Restart Home Assistant when prompted.
## Configuration
In Home Assistant, go to Settings > Devices & Services.
Click the Add Integration button.
Search for "DT20HBW Monitor" and select it.
A configuration form will appear.

Device ID: (Required) Enter the Device ID you obtained earlier.
Local Key: (Required) Enter the Local Key for the device.
Host (IP Address): (Optional) Leave this blank to use auto-discovery. Only fill this in if auto-discovery fails.
Protocol Version: (Required) Select the protocol version for your device. 3.5 is a common default for newer devices.
Click Submit. The integration will set up the device and its entities.
## Entities Created

The integration will create a device with the following entities:
| Platform | Name                        | Description                                     |
| :------- | :-------------------------- | :---------------------------------------------- |
| Sensor   | Voltage                     | Real-time battery voltage (V)                   |
| Sensor   | Current                     | Real-time charge/discharge current (A)          |
| Sensor   | Power                       | Real-time charge/discharge power (W)            |
| Sensor   | Battery                     | State of Charge (%)                             |
| Sensor   | NTC Temperature             | External probe temperature (°C)                 |
| Sensor   | CPU Temperature             | Internal device temperature (°C)                |
| Sensor   | Total Energy                | Cumulative energy measured (kWh)                |
| Sensor   | Total Capacity              | Cumulative capacity measured (Ah)               |
| Sensor   | Alarm Status                | Current alarm state (e.g., `ovp`, `otp`)        |
| Sensor   | Resistance                  | Calculated resistance (Ω)                       |
| Switch   | Relay Switch                | Controls the main output relay.                 |
| Switch   | Fast Data Refresh           | Toggles between 1s and 60s data refresh rate.   |
| Number   | Over Voltage Protection     | Sets the OVP threshold (V).                     |
| Number   | Low Voltage Protection      | Sets the LVP threshold (V).                     |
| Number   | Over Power Protection       | Sets the OPP threshold (W).                     |
| Number   | Over Temperature Protection | Sets the OTP threshold (°C).                    |
| Number   | Screen Brightness           | Sets the screen brightness when active.         |
| Number   | Standby Brightness          | Sets the screen brightness when in standby.     |
| Number   | Standby Time                | Sets the time until the screen enters standby.  |
| Number   | Current Threshold           | Minimum current to be considered "active" (mA). |
| Number   | Reporting Interval          | How often the device sends data (s).            |
| Select   | Language                    | Sets the device's on-screen language.           |
| Select   | Diverter Size               | Configures the measurement shunt size (A).      |
| Select   | Display Style               | Changes the on-screen display layout.           |
| Button   | Data Reset                  | Resets cumulative energy/capacity data.         |
| Button   | WiFi Reset                  | Resets the device's Wi-Fi configuration.        |
| Button   | Factory Reset               | Resets all settings to factory defaults.        |
| Button   | Exit Menu                   | Exits the settings menu on the device screen.   |

## Troubleshooting
Discovery Failed: If you leave the "Host" field blank and receive a "discovery failed" error, it's likely due to your network configuration (e.g., VLANs, or Home Assistant running in a Docker container not in host mode).
Solution: Find the device's local IP address from your router and enter it manually in the "Host" field during setup.
Discovery Port in Use: If you receive an error that the "discovery port is in use," it means another Tuya integration (like the official Tuya integration or LocalTuya) is already running a discovery scan.
Solution: You must use the manual IP entry method. Find the device's IP from your router and enter it in the "Host" field.
## Contributing
Contributions are welcome! If you have an idea for an improvement or find a bug, please open an issue to discuss it.
## Disclaimer
This is a third-party integration and is not officially supported by Tuya or the device manufacturer. Use at your own risk.
