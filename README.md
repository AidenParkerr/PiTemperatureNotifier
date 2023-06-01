# Temperature Notifier

Temperature Monitor is a Python script that automates the monitoring of a device's temperature and sends a notification when the temperature exceeds predefined thresholds. It uses the Telegram API to send these notifications.

## Features
- Automatically monitors the device's temperature, which can be especially useful when run as a cron job.
- Logs the temperature monitoring process, with logs viewable in temps.log.
- Prevents multiple simultaneous runs of the script using a lock file mechanism.
- Sends notifications via Telegram when temperature thresholds are exceeded.
- Provides customizable messages for different temperature thresholds.
- Gracefully handles interruptions and script termination, sending a notification when the monitor is stopped.
- Accepts command line arguments for configuration file location and device name.

## Requirements

The script requires the following Python packages:

- os
- requests
- configparser
- logging
- time
- signal
- fcntl
- argparse

These packages are included in the standard Python 3 library.

## Configuration

You need to create a `config.ini` file in the same directory as the script. This file should contain your Telegram bot token and chat ID in the following format:
```
[Telegram]
bot_token = "your_bot_token"
chat_id = "your_chat_id"
```


Please note that the `config.ini` file should not be shared or uploaded to public repositories as it contains sensitive data.

## Usage

You can run the script with the following command:

```
python3 temperature_monitor.py --config_file path_to_config_file --device_name your_device_name
```

The `--config_file` argument is required and should be the path to your `config.ini` file. The `--device_name` argument is optional, with "device1" as the default value.

