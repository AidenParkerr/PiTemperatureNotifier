import os
import logging
import requests
import configparser
from urllib.parse import quote

class TempMonitor():
    def __init__(self, temp_thresholds: dict=None):
        self._init_logger()
        self.load_telegram_config()
        self.temp_thresholds = temp_thresholds
        self.lock_file = "/tmp/temp_monitor.lock"
        if self.temp_thresholds is None:
            self.temp_thresholds = {
                80.0: "TEMPERATURE IS VERY HIGH > 80c:",
                70.0: "TEMPERATURE IS HIGH > 70c:",
                60.0: "TEMPERATURE IS CLIMBING > 60c. Keep an eye on it:",
            }

    def _init_logger(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temps.log')
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

    def load_telegram_config(self):
        self.logger.info("Loading Telegram bot token and chat id...")
        
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        config.read(config_path)

        self.bot_token = config['Telegram']['bot_token'].strip('"')
        self.chat_id = config['Telegram']['chat_id'].strip('"')

        if self.bot_token is None or self.chat_id is None:
            self.logger.error("Telegram bot token or chat id not found. Exiting...")
            exit(1)
        self.logger.info("Telegram bot token and chat id loaded.")

    def get_temp(self) -> float:
        self.logger.info("Retrieving temperature...")
        try:
            temp = os.popen("vcgencmd measure_temp").readline()
            temp: float = float(temp.replace("temp=","").replace("'C\n",""))
        except Exception as e:
            self.logger.error("Failed to get temperature", exc_info=True)
            return None

        self.logger.info(f"Temperature Received. Temp: {temp}c.")
        return temp

    def send_notification(self, body: str) -> None:
        self.logger.info("Attempting to send notification...")
        try:
            # URL-encode the body text
            body = quote(body)
            send_text = f'https://api.telegram.org/bot{self.bot_token}/sendMessage?chat_id={self.chat_id}&parse_mode=Markdown&text={body}'
            print(send_text)
            response = requests.get(send_text)
            if response.status_code == 200:
                self.logger.info("Notification sent.")
            else:
                self.logger.error(f"Failed to send notification, status code: {response.status_code}")
        except Exception as e:
            self.logger.error("Failed to send notification", exc_info=True)

    def monitor_temp(self, temp: float) -> None:
        if temp is None:
            self.logger.error("Temperature is None, skipping...")
            return
        temp_exceeded = False
        for threshold, message in self.temp_thresholds.items():
            if temp > threshold:
                self.logger.warning(f"Temperature exceeds {threshold}c")
                markdown_message = f"*{message}*\nCurrent Temp: *{temp}c*!"
                self.send_notification(markdown_message)
                temp_exceeded = True
                break

        if not temp_exceeded:
            self.logger.info(f"Temperature optimal: {temp}c.")

    def run(self) -> None:
        if os.path.exists(self.lock_file):
            self.logger.error("Temp monitor is already running. Exiting...")
            exit(1)

        with open(self.lock_file, "w") as f:
            f.write("lock")

        try:
            temp: float = self.get_temp()
            self.monitor_temp(temp)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received. Exiting...")
            self.send_notification("Temp monitor stopped.")
        finally:
            os.remove(self.lock_file)

if __name__ == '__main__':
    temp_monitor = TempMonitor()
    temp_monitor.run()
