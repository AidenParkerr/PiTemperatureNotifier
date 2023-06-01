import os
import requests
import configparser
import logging
import time
import signal
import fcntl
import argparse


class TempMonitor():
    def __init__(self, config_path: str, device_name: str,
                 temp_thresholds: dict = None) -> None:
        self.temp_thresholds = temp_thresholds
        self.config_path = config_path
        self.device_name = device_name
        self.lock_file = "/tmp/TempMonitor.lock"
        self._init_logger()
        self._load_telegram_config()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        if self.temp_thresholds is None:
            self.temp_thresholds = {
                80.0: "TEMPERATURE IS VERY HIGH",
                70.0: "TEMPERATURE IS HIGH",
                60.0: "TEMPERATURE IS CLIMBING. Keep an eye on it",
            }

    def _read_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_path)

        if not config.has_section(
                'Telegram') or "bot_token" not in config['Telegram'] or "chat_id" not in config['Telegram']:
            self.logger.critical(
                "Telegram bot token or chat ID not found in config file. Exiting...")

            self.logger.info(
                f"Read from config.ini: `{config.read(self.config_path)}`")
            raise ValueError(
                "Telegram bot token or chat ID not found in config.ini file. This could be due to the format of the config file.")

        self.bot_token = config['Telegram']['bot_token'].strip('"')
        self.chat_id = config['Telegram']['chat_id'].strip('"')

    def _init_logger(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        log_path = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)),
            'temps.log')
        file_handler = logging.FileHandler(log_path)
        console_handler = logging.StreamHandler()

        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_format = logging.Formatter(
            '%(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        console_handler.setFormatter(console_format)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _signal_handler(self, signum, frame) -> None:
        if signum == signal.SIGINT:
            self.logger.info("Received SIGINT signal. Exiting...")
        elif signum == signal.SIGTERM:
            self.logger.info("Received SIGTERM signal. Exiting...")
        self.send_notification("*Temperature Notifier Stopped.*")
        exit(0)

    def _load_telegram_config(self):
        self.logger.info("Loading Telegram bot token and chat ID...")
        self._read_config()

        if self.bot_token is None or self.chat_id is None:
            self.logger.critical(
                "Telegram bot token or chat ID not found. Exiting...")
            raise ValueError("Telegram bot token or chat ID not found.")

        self.logger.info("Telegram bot token and chat ID loaded.")

    def send_notification(self, body: str) -> None:
        try:
            self.logger.info(f"Sending Notification to Telegram: '{body}'")
            tg_api_link = f"https://api.telegram.org/bot{self.bot_token}/sendMessage?chat_id={self.chat_id}&parse_mode=Markdown&text={body}"
            response = requests.get(tg_api_link)
            if response.status_code == 200:
                self.logger.info("Notification sent to Telegram.")
            else:
                self.logger.error(
                    f"Failed to send notification to Telegram, status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Failed to send notification to Telegram: {e}",
                exc_info=True)

    def get_temp(self) -> float:
        self.logger.info("Retriving temperature...")
        try:
            temp = os.popen("vcgencmd measure_temp").readline()
            temp_float_val: float = float(
                temp.replace(
                    "temp=", "").replace(
                    "'C\n", ""))
        except Exception as e:
            self.logger.error(f"Failed to get temperature: {e}", exc_info=True)
            return None

        self.logger.info(f"Temperature Recieved. Temp: {temp_float_val}c.")
        return temp_float_val

    def monitor_temp(self, temp: float) -> None:
        if temp is None:
            self.logger.error("Temperature is None, skipping...")
            return

        for threshold, message in self.temp_thresholds.items():
            if temp > threshold:
                self.logger.warning(f"Temperature exceeds {threshold}c")
                self.send_notification(
                    f"*WARNING - TEMPERATURE EXCEEDS {threshold}c.*\n{message}: {temp}c!")
                break

    def run(self) -> None:
        try:
            lock_file_descriptor = os.open(
                self.lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except OSError as e:
            self.logger.error(
                f"Failed to create lock file: {e}", exc_info=True)
            return

        try:
            fcntl.lockf(lock_file_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as e:
            self.logger.error(
                f"An Instance of this script is already running: {e}. Exiting...")
            return

        try:
            temp: float = self.get_temp()
            # Wait for 5 seconds before checking again if `temp`` is None.
            if temp is None:
                time.sleep(5)
                temp: float = self.get_temp()
                if temp is None:
                    self.logger.error("Failed to get temperature. Exiting...")
                    raise ValueError("Failed to get temperature from device.")
            self.monitor_temp(temp)
        except KeyboardInterrupt:
            self.logger.info("Keyboard Interrupt received. Exiting...")
            self.send_notification("*Temperature Monitor stopped.*")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.send_notification(
                f"Temperature Notifier experienced an unexpected erro:r: {e}")
        finally:
            # Release the lock on the lock file and delete it.
            self.logger.info("Removing lock file...")
            try:
                os.close(lock_file_descriptor)
                os.remove(self.lock_file)
                self.logger.info("Lock file removed.")
            except Exception as e:
                self.logger.error(
                    f"Failed to remove lock file: {e}",
                    exc_info=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Temperature Monitor")
    parser.add_argument(
        "--config_file",
        type=str,
        help="Config file location",
        required=True)
    parser.add_argument(
        "--device_name",
        type=str,
        default="device1",
        help="Device name")

    args = parser.parse_args()

    temp_monitor = TempMonitor(
        config_path=args.config_file,
        device_name=args.device_name)
    temp_monitor.run()
