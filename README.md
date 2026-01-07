# Ultrahuman Home Assistant Integration

Home Assistant integration for Ultrahuman health and fitness data.

## Features

- Fetches daily metrics from Ultrahuman API
- Automatic updates every 15 minutes
- Dynamic sensor creation based on available data
- Config Flow for easy setup

## Installation

### Via HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz) is installed
2. Go to HACS → Integrations
3. Click "Custom repositories"
4. Add this repository URL
5. Select category "Integration"
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ultrahuman` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Ultrahuman" and follow the setup instructions

## Configuration

### Getting Your Personal API Token

1. Log in to your Ultrahuman account
2. Navigate to Settings → API or Developer Settings
3. Generate a Personal API Token
4. Copy the token

### Setting Up the Integration

1. In Home Assistant, go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Ultrahuman"
4. Enter your Personal API Token
5. Click "Submit"

The integration will automatically validate your token and create sensors for your daily metrics.

## Sensors

The integration automatically creates sensors based on the data returned by the Ultrahuman API. Sensors are created dynamically, so the exact sensors available depend on your data.

Common sensors may include:
- Daily metrics
- Health data
- Fitness metrics

## Troubleshooting

### Invalid API Token Error

- Verify that your Personal API Token is correct
- Make sure the token hasn't expired
- Check that you have the necessary permissions

### Cannot Connect Error

- Check your internet connection
- Verify that the Ultrahuman API is accessible
- Check Home Assistant logs for detailed error messages

## Development

### Requirements

- Python 3.10+
- Home Assistant 2024.1.0 or later
- aiohttp

### Project Structure

```
custom_components/
  ultrahuman/
    __init__.py          # Main integration setup
    manifest.json         # Integration manifest
    config_flow.py       # Config flow for API token
    coordinator.py       # Data update coordinator
    sensor.py            # Sensor platform
    const.py             # Constants
    strings.json         # Translations
```

## License

This project is licensed under the MIT License.

## Support

For issues and feature requests, please open an issue on GitHub.
