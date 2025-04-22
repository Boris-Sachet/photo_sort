import configparser
import logging
import os
import shutil
from os.path import dirname, abspath
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)


def extract_paths(paths: str) -> List[Path]:
    """Extract paths from a config string"""
    result = []
    if paths.strip() != '':
        for path in paths.split(','):
            result.append(Path(path.strip()))
    return result


def extract_list(string: str) -> List[str]:
    """Extract a list of strings from a config string"""
    result = []
    if string.strip() != '':
        for string in string.split(','):
            result.append(string.strip())
    return result


def extract_bool(boolean: str) -> bool:
    """Extract a boolean from a config string"""
    return boolean.strip().lower() in ["true", "yes", "y"]


class SourceConfig:
    def __init__(self, source_name: str, source_path: str, source_ignore: str, use_subdir: str, subdir_names: str):
        self.name = source_name.split('.')[1]
        self.source_path = Path(source_path) if source_path else None
        self.source_ignore = extract_list(source_ignore)
        self.use_subdir = extract_bool(use_subdir)
        self.subdir_names = extract_list(subdir_names)


class Config:
    private_storage_paths: List[Path] = []
    public_storage_paths: List[Path] = []
    storage_ignore: List[str] = []
    use_subdir_for_public_storages: bool = False
    public_storages_subdir_names: List[str] = []
    log_level: str = 'INFO'
    data_keys: List[str] = []
    test_mode: bool = False
    pushbullet_api_key: str = ''
    pushbullet_encryption_key: str = ''
    pushover_user: str = ''
    pushover_token: str = ''
    sources: List[SourceConfig] = []

    @classmethod
    def init(cls):
        """
        This method initialize the application config and create the config directory and the config file with default
         values if it does not exist.
        """
        config_path = Path(f"{os.path.expanduser('~')}/.config/photosort/")
        config_file_name = "config.ini"
        os.makedirs(config_path, 0o744, True)
        if not (config_path / config_file_name).is_file():
            cls.create_config_file(config_path, config_file_name)

        cls.parse_config_file(config_path, config_file_name)

    @staticmethod
    def create_config_file(config_path: Path, config_file: str):
        logging.info("Creating default configuration file")
        # Insert default config if file does not exist
        shutil.copy(src=Path(dirname(abspath(__file__)), "config_template.ini"), dst=config_path / config_file)

    @classmethod
    def parse_config_file(cls, config_path: Path, config_file_name: str):
        # Read config
        config_file = configparser.ConfigParser()
        config_file.read(config_path / config_file_name)

        try:
            # Load config from conf file
            # General settings
            cls.username = config_file["general"]["user_name"].strip()
            cls.log_level = config_file["general"]["log_level"].strip()
            cls.data_keys = extract_list(config_file["general"]["data_keys"])
            cls.test_mode = extract_bool(config_file["general"]["test_mode"])
            cls.pushbullet_api_key = config_file["general"]["pushbullet_api_key"].strip()
            cls.pushbullet_encryption_key = config_file["general"]["pushbullet_encryption_key"].strip()
            cls.pushover_user = config_file["general"]["pushover_user"].strip()
            cls.pushover_token = config_file["general"]["pushover_token"].strip()

            # Storage settings
            cls.private_storage_paths = extract_paths(config_file["storage"]["private_storage_paths"])
            cls.public_storage_paths = extract_paths(config_file["storage"]["public_storage_paths"])
            cls.storage_ignore = extract_list(config_file["storage"]["storage_ignore"])
            cls.use_subdir_for_public_storages = extract_bool(config_file["storage"]["use_subdir_for_public"])
            cls.public_storages_subdir_names = extract_list(config_file["storage"]["subdir_names"])
            cls.move_files_to_storage = extract_bool(config_file["storage"]["move_files_to_storage"])

            # Source settings
            sources_configs = [section for section in config_file.keys() if section.startswith("source.")]
            for source in sources_configs:
                cls.sources.append(SourceConfig(
                    source_name=source,
                    source_path=config_file[source]["source_path"],
                    source_ignore=config_file[source]["source_ignore"],
                    use_subdir=config_file[source]["use_subdir"],
                    subdir_names=config_file[source]["subdir_names"],
                ))
        except KeyError as error:
            LOGGER.error(f"Error missing configuration in config file: {error}")
