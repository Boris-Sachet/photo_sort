import configparser
import logging
import os
import shutil
from os.path import dirname, abspath
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)


class SourceConfig:
    def __init__(self, source_path: str, source_ignore: str, use_subdir: str, subdir_names: str):
        self.source_path = Path(source_path)
        self.source_ignore = [item.strip() for item in source_ignore.split(',')]
        self.use_subdir = use_subdir.strip().lower() in ["true", "yes", "y"]
        self.subdir_names = [item.strip() for item in subdir_names.split(',')]


class Config:
    private_storage_paths: List[Path] = []
    public_storage_paths: List[Path] = []
    storage_ignore: List[Path] = []
    use_subdir_for_public_storages: bool = False
    public_storages_subdir_names: List[str] = []
    log_level: str = 'INFO'
    data_keys: List[str] = []
    test_mode: bool = False
    pushbullet_api_key: str = ''
    pushbullet_encryption_key: str = ''
    sources: List[SourceConfig] = []

    @classmethod
    def init(cls):
        """
        This method initialize the application config and create the config directory and the config file with default
         values if it does not exist.
        """
        config_path = Path(f"{os.path.expanduser('~')}/.config/photosort/")
        config_file_name = "config"
        os.makedirs(config_path, 0o744, True)
        if not (config_path / config_file_name).is_file():
            cls.create_config_file(config_path, config_file_name)

        cls.parse_config_file(config_path, config_file_name)

    @staticmethod
    def create_config_file(config_path: Path, config_file: str):
        # TODO copy template file instead of this
        logging.info("Creating default configuration file")
        # Insert default config if file does not exist
        shutil.copy(src=Path(dirname(abspath(__file__)), "config_template.ini"), dst=config_path / config_file)

    @classmethod
    def parse_config_file(cls, config_path: Path, config_file_name: str):
        # Read config
        config_file = configparser.ConfigParser()
        config_file.read(config_path / config_file_name)

        # Load config from conf file
        # General settings
        cls.private_storage_paths = cls.__extract_paths(config_file["general"]["private_storage_paths"])
        cls.public_storage_paths = cls.__extract_paths(config_file["general"]["public_storage_paths"])
        cls.storage_ignore = cls.__extract_paths(config_file["general"]["storage_ignore"])
        cls.use_subdir_for_public_storages = cls.__extract_bool(config_file["general"]["use_subdir_for_public"])
        cls.public_storages_subdir_names = cls.__extract_list(config_file["general"]["subdir_names"])
        cls.log_level = config_file["general"]["log_level"].strip()
        cls.data_keys = cls.__extract_list(config_file["general"]["data_keys"])
        cls.test_mode = cls.__extract_bool(config_file["general"]["test_mode"])
        cls.pushbullet_api_key = config_file["general"]["pushbullet_api_key"].strip()
        cls.pushbullet_encryption_key = config_file["general"]["pushbullet_encryption_key"].strip()

        # Source settings
        cls.sources = [SourceConfig(
            source_path=config_file["source.photo"]["source_path"],
            source_ignore=config_file["source.photo"]["source_ignore"],
            use_subdir=config_file["source.photo"]["use_subdir"],
            subdir_names=config_file["source.photo"]["subdir_names"],
        )]

    @staticmethod
    def __extract_paths(paths: str) -> List[Path]:
        """Extract paths from a config string"""
        result = []
        if paths.strip() != '':
            for path in paths.split(','):
                result.append(Path(path.strip()))
        return result

    @staticmethod
    def __extract_list(string: str) -> List[str]:
        """Extract a list of strings from a config string"""
        result = []
        if string.strip() != '':
            for string in string.split(','):
                result.append(string.strip())
        return result

    @staticmethod
    def __extract_bool(boolean: str) -> bool:
        """Extract a boolean from a config string"""
        return boolean.strip().lower() in ["true", "yes", "y"]
