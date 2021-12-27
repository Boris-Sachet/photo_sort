import configparser
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from PIL import Image, ExifTags
# from pprint import pprint
import ffmpeg

from dated_folder import DatedFolder


def init(config_path: str, config_file: str):
    """
    This method initialize the application and create the config directory and the config file with default values
    if it does not exist.
    :param config_path: Configuration path
    :param config_file: Configuration file name
    """
    os.makedirs(config_path, 0o744, True)
    if not os.path.isfile(os.path.join(config_path, config_file)):
        logging.info("Creating default configuration file")
        # Insert default config if file does not exist
        config = {
            "source_path": "/volume1/photo/phone/DCIM/Camera # Files source folder path",
            "source_ignore": " # Comma separated list of files names to ignore",
            "storage_paths": "/volume1/photo/photo, /volume1/photo/photo/Mélo # Comma separated list of path to look for storage folders",
            "storage_ignore": " # Comma separated list of path to ignore",
            "log_level": "info # Choose between debug, info, warning, error, critical",
            "data_keys": "DateTimeOriginal, DateTime, creation_time # Comma separated list of metadata param to look for retrieving the date of the file"
        }
        configF = open(os.path.join(config_path, config_file), "a")
        configF.write("[conf]\n")
        for key, value in config.items():
            configF.write(f"{key} = {value}\n")
        configF.close()


def get_pic_meta_date(path: str, name: str, data_keys: list) -> datetime:
    try:
        img = Image.open(f"{path}{name}")
        exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}
        for key in data_keys:
            if key in exif.keys():
                return datetime.strptime(exif.get(key).split(' ')[0], "%Y:%m:%d")
        else:
            return None
    except Exception as e:
        logger.error(f"{name} metadata reading : {e}")


def get_vid_meta_date(path: str, name: str, data_keys: list) -> datetime:
    file = f"{path}{name}"
    try:
        vid = ffmpeg.probe(file)['streams']
        for key in data_keys:
            if key in vid[0]['tags']:
                return datetime.strptime(vid[0]['tags'].get(key).split('T')[0], "%Y-%m-%d")
        else:
            return None
    except ffmpeg.Error as e:
        logger.error(f"{name} metadata reading : {e.stderr}")


def list_folders(paths: list, ignore: list) -> list:
    results = []
    for path in paths:
        for name in os.listdir(path):
            if os.path.isdir(f"{path}{name}") and name not in ignore:
                result = DatedFolder(name, path, data_logger)
                if result.isValid:
                    results.append(result)
    return results


def sort_file(source_path: str, file: str, date: datetime, storage_paths: list):
    if date is not None:
        for path in storage_paths:
            if path.begin <= date <= path.end:
                if not os.path.isfile(f"{source_path}"):
                    logger.debug(f"Moving '{file}' to '{path.name}'")
                    return
                else:
                    return


def log_level(level: str) -> int:
    return {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }.get(level, logging.INFO)


def main():
    config_path = f"{os.path.expanduser('~')}/.config/photosort/"
    config_file = "config"
    init(config_path, config_file)

    # Read config
    config = configparser.ConfigParser()
    config.read(os.path.join(config_path, config_file))

    # Configure logs

    log_lv = log_level(config["conf"]["log_level"].split('#')[0].strip())
    logger.setLevel(log_lv)
    data_logger.setLevel(log_lv)

    # Load config from conf file
    logger.info(f"Execution start at {datetime.now()}")
    data_keys = [item.strip() for item in config["conf"]["data_keys"].split('#')[0].split(',')]
    source_path = config["conf"]["source_path"].split('#')[0].strip()
    if not source_path.endswith('/'):
        source_path += '/'
    source_ignore = [item.strip() for item in config["conf"]["source_ignore"].split('#')[0].split(',')]
    storage_paths = [item.strip() for item in config["conf"]["storage_paths"].split('#')[0].split(',')]
    storage_ignore = [item.strip() for item in config["conf"]["storage_ignore"].split('#')[0].split(',')]

    # Read folders and sort files
    dir_list = list_folders(storage_paths, storage_ignore)
    for name in os.listdir(source_path):
        if os.path.isfile(f"{source_path}{name}") and name not in source_ignore:
            if name.endswith(".mp4"):
                # print(f"{name} : {get_vid_meta_date(source_path, name, data_keys)}")
                sort_file(source_path, name, get_vid_meta_date(source_path, name, data_keys), dir_list)
            elif name.endswith(".jpg"):
                # print(f"{name} : {get_pic_meta_date(source_path, name, data_keys)}")
                sort_file(source_path, name, get_pic_meta_date(source_path, name, data_keys), dir_list)
            else:
                logging.error(f"Unsortable file '{name}'")
    logger.info(f"Execution end at {datetime.now()}")


# MAIN
if __name__ == '__main__':
    logging.basicConfig(filename="log")
    log_handler = RotatingFileHandler("log", maxBytes=5 * 1024 * 1024)
    logger = logging.getLogger(__name__)
    data_logger = logging.getLogger("datafold")
    main()
