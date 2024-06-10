import configparser
import logging
import os
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class Config:
    def __init__(self):
        config_path = Path(f"{os.path.expanduser('~')}/.config/photosort/")
        config_file_name = "config"
        self.init(config_path, config_file_name)

        # Read config
        config_file = configparser.ConfigParser()
        config_file.read(config_path/config_file_name)

        # Configure logs
        self.log_lv = config_file["conf"]["log_level"].split('#')[0].strip()

        # Load config from conf file
        self.data_keys = [item.strip() for item in config_file["conf"]["data_keys"].split('#')[0].split(',')]
        self.source_path = Path(config_file["conf"]["source_path"].split('#')[0].strip())
        self.source_ignore = [Path(item.strip()) for item in config_file["conf"]["source_ignore"].split('#')[0].split(',')]
        self.storage_paths = [Path(item.strip()) for item in config_file["conf"]["storage_paths"].split('#')[0].split(',')]
        self.storage_ignore = [Path(item.strip()) for item in config_file["conf"]["storage_ignore"].split('#')[0].split(',')]
        self.test_mode = False if config_file["conf"]["test_mode"].split('#')[0].strip().lower() == "false" else True
        self.pushbullet_api_key = config_file["conf"]["pushbullet_api_key"].split('#')[0].strip()
        self.pushbullet_encryption_key = config_file["conf"]["pushbullet_encryption_key"].split('#')[0].strip()

    @staticmethod
    def init(config_path: Path, config_file: str):
        """
        This method initialize the application and create the config directory and the config file with default values
        if it does not exist.
        :param config_path: Configuration path
        :param config_file: Configuration file name
        """
        os.makedirs(config_path, 0o744, True)
        if not (config_path/config_file).is_file():
            logging.info("Creating default configuration file")
            # Insert default config if file does not exist
            config = {
                "source_path": "/volume1/photo/phone/DCIM/Camera # Files source folder path",
                "source_ignore": " # Comma separated list of files names to ignore",
                "source_messenger": "",
                "source_whatsapp": "",
                "source_element": "",
                "storage_paths": "/volume1/photo/photo, /volume1/photo/photo/Mélo # Comma separated list of path to look for storage folders",
                "storage_ignore": " # Comma separated list of path to ignore",
                "log_level": "info # Choose between debug, info, warning, error, critical",
                "data_keys": "DateTimeOriginal, DateTime, creation_time # Comma separated list of metadata param to look for retrieving the date of the file",
                "test_mode": "False # True / False, False to actually move the files to the storage, True to just preted to do it and still write the log (to make sure everything is ok before copiying files everywhere)",
                "pushbullet_api_key": " # Get it here : https://www.pushbullet.com/#settings/account",
                "pushbullet_encryption_key": "",
            }
            with (config_path/config_file).open("a") as file:
                file.write("[conf]\n")
                for key, value in config.items():
                    file.write(f"{key} = {value}\n")
