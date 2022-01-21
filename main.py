import shutil
import socket
import sys
import configparser
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from PIL import Image, ExifTags
# from pprint import pprint
import ffmpeg

from dated_folder import DatedFolder
from pushbullet import Pushbullet


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
            "data_keys": "DateTimeOriginal, DateTime, creation_time # Comma separated list of metadata param to look for retrieving the date of the file",
            "test_mode": "False # True / False, False to actually move the files to the storage, True to just preted to do it and still write the log (to make sure everything is ok before copiying files everywhere)",
            "pushbullet_api_key": " # Get it here : https://www.pushbullet.com/#settings/account",
            "pushbullet_encryption_key": "",
        }
        configF = open(os.path.join(config_path, config_file), "a")
        configF.write("[conf]\n")
        for key, value in config.items():
            configF.write(f"{key} = {value}\n")
        configF.close()


def get_date_from_name(name: str) -> datetime:
    for string in name.split('_'):
        if len(string) == 8:
            try:
                result = datetime.strptime(string, "%Y%m%d")
                return result
            except ValueError:
                pass
                logger.debug(f"{name} : Can't convert '{string}' to datetime")
    else:
        logger.error(f"{name} : No date found in filename")
        return None


def get_pic_meta_date(path: str, name: str, data_keys: list) -> datetime:
    # Can also be done with:
    # import exifread
    # f = open(file, 'rb')
    # tags = exifread.process_file(f)
    try:
        img = Image.open(f"{path}{name}")
        exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}
        for key in data_keys:
            if key in exif.keys():
                return datetime.strptime(exif.get(key).split(' ')[0], "%Y:%m:%d")
    except Exception as e:
        file_date = get_date_from_name(name)
        if file_date is None:
            logger.error(f"{name} metadata reading : {e}")
        else:
            return file_date
    return None


def get_vid_meta_date(path: str, name: str, data_keys: list) -> datetime:
    file = f"{path}{name}"
    try:
        vid = ffmpeg.probe(file)['streams']
        for key in data_keys:
            if key in vid[0]['tags']:
                return datetime.strptime(vid[0]['tags'].get(key).split('T')[0], "%Y-%m-%d")
    except ffmpeg.Error as e:
        file_date = get_date_from_name(name)
        if file_date is None:
            logger.error(f"{name} metadata reading : {e.stderr}")
        else:
            return file_date
    except Exception as e:
        file_date = get_date_from_name(name)
        if file_date is None:
            logger.error(f"{name} metadata reading : {e}")
        else:
            return file_date
    return None


def list_folders(paths: list, ignore: list) -> list:
    """
    List all storage folders in given paths and create a list of dated_folder objects with every valid data folder found
    Data folder is valid only if it start with a date that this scrip can read
    :param paths: List of paths in which to look for storage folder
    :param ignore: list of folder names to ignore
    :return: List of dated_folder object containing the info of every valid folder found
    """
    results = []
    for path in paths:
        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path, name)) and name not in ignore:
                result = DatedFolder(name, path, data_logger)
                if result.isValid:
                    results.append(result)
    logger.info(f"{len(results)} storage folder found")
    return results


def sort_file(source_path: str, file: str, date: datetime, storage_paths: list, test_mode: bool) -> bool:
    if date is not None:
        for folder in storage_paths:
            if folder.begin <= date <= folder.end:
                if not os.path.isfile(os.path.join(folder.get_path(), file)):
                    if not test_mode:
                        copied_path = shutil.copy(os.path.join(source_path, file), folder.get_path())
                        logger.info(f"Copied '{file}' to '{copied_path}'")
                    else:
                        logger.info(f"Copied '{file}' to '{folder.name}' (test mode)")
                    return True
                else:
                    logger.debug(f"File '{file}' is already sorted in '{folder.name}', nothing to do")
                    return False
    else:
        logger.error(f"No date found for '{file}', can't sort it")
        return False


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
    source_ignore = [item.strip() for item in config["conf"]["source_ignore"].split('#')[0].split(',')]
    storage_paths = [item.strip() for item in config["conf"]["storage_paths"].split('#')[0].split(',')]
    storage_ignore = [item.strip() for item in config["conf"]["storage_ignore"].split('#')[0].split(',')]
    test_mode = False if config["conf"]["test_mode"].split('#')[0].strip().lower() == "false" else True
    pushbullet_api_key = config["conf"]["pushbullet_api_key"].split('#')[0].strip()
    pushbullet_encryption_key = config["conf"]["pushbullet_encryption_key"].split('#')[0].strip()

    # Pushbullet auth
    if pushbullet_api_key is not None or pushbullet_api_key != "":
        pb = Pushbullet(pushbullet_api_key, pushbullet_encryption_key)

    # Fix paths in case user and dev are dumbasses
    if not source_path.endswith('/'):
        source_path += '/'
    for path in storage_paths:
        if not path.endswith('/'):
            storage_paths[storage_paths.index(path)] += '/'

    # Read folders and sort files
    count = 0
    sorted_count = 0
    unsortable_count = 0
    dir_list = list_folders(storage_paths, storage_ignore)
    if len(dir_list) > 0:
        for name in os.listdir(source_path):
            count += 1
            if os.path.isfile(f"{source_path}{name}") and name not in source_ignore:
                if name.endswith(".mp4"):
                    if sort_file(source_path, name, get_vid_meta_date(source_path, name, data_keys), dir_list, test_mode):
                        sorted_count += 1
                elif name.endswith(".jpg"):
                    if sort_file(source_path, name, get_pic_meta_date(source_path, name, data_keys), dir_list, test_mode):
                        sorted_count += 1
                else:
                    unsortable_count += 1
                    logger.error(f"Unsortable file '{name}'")
    else:
        logger.error("No storage directories found")
    if pushbullet_api_key is not None or pushbullet_api_key != "":
        pb.push_note(f"{socket.gethostname()} - PhotoSort executed",
                     f"{sorted_count} of {count} files sorted, {unsortable_count} unsortables files")
    logger.info(f"Execution end at {datetime.now()}")


# MAIN
if __name__ == '__main__':
    sys.path.append("/var/packages/MediaServer/target/bin/ffmpeg")
    sys.path.append("/var/packages/MediaServer/target/bin/ffprobe")
    log_handler = RotatingFileHandler("log", maxBytes=5 * 1024 * 1024)
    log_handler.setFormatter(logging.Formatter('%(levelname)-7s %(asctime)s %(name)s: %(message)s'))
    logger = logging.getLogger(__name__)
    data_logger = logging.getLogger("datafold")
    logger.addHandler(log_handler)
    data_logger.addHandler(log_handler)
    main()
