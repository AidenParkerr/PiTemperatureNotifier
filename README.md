# Temperature Notifier

The Temperature Notifier is a Python script that automates the monitoring of the Pi's temperature and sends a notification when the temperature exceeds the thresolds set. This script also utilizes the Telegram API to send notifications about the Temperature status.

## Features

- Automatically monitors the temperature of the Pi (when used as a cronjob.)
- Logs the backup process, logging can be viewed in `temps.log`.
- Prevents simultaneous runs of the script by using a lock file mechanism.
- Sends notifications about the backup process via Telegram.

## Requirements

The script requires the following Python packages:
- `configparser`
- `urllib`
- `requests`
- `logging`
- `os`

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
python3 temperature_notifier.py
```

