import shutil
import socket
import sys
import logging
import os
from datetime import datetime
import loging_config  # noqa: F401

from PIL import Image, ExifTags
import ffmpeg

from config import Config
from dated_folder import DatedFolder
from pushbullet import Pushbullet

LOGGER = logging.getLogger(__name__)


def get_date_from_name(name: str) -> datetime:
    for string in name.split('_'):
        if len(string) == 8:
            try:
                result = datetime.strptime(string, "%Y%m%d")
                return result
            except ValueError:
                pass
                LOGGER.debug(f"{name} : Can't convert '{string}' to datetime")
    else:
        LOGGER.error(f"{name} : No date found in filename")
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
            LOGGER.error(f"{name} metadata reading : {e}")
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
            LOGGER.error(f"{name} metadata reading : {e.stderr}")
        else:
            return file_date
    except Exception as e:
        file_date = get_date_from_name(name)
        if file_date is None:
            LOGGER.error(f"{name} metadata reading : {e}")
        else:
            return file_date
    return None


def list_folders(paths: list, ignore: list) -> list:
    """
    List all storage folders in given paths and create a list of dated_folder objects with every valid data folder found
    Data folder is valid only if it starts with a date that this scrip can read
    :param paths: List of paths in which to look for storage folder
    :param ignore: list of folder names to ignore
    :return: List of dated_folder object containing the info of every valid folder found
    """
    results = []
    for path in paths:
        for name in os.listdir(path):
            if os.path.isdir(os.path.join(path, name)) and name not in ignore:
                result = DatedFolder(name, path)
                if result.isValid:
                    results.append(result)
    LOGGER.info(f"{len(results)} storage folder found")
    return results


def sort_file(source_path: str, file: str, date: datetime, storage_paths: list, test_mode: bool) -> bool:
    if date is not None:
        for folder in storage_paths:
            if folder.begin <= date <= folder.end:
                if not os.path.isfile(os.path.join(folder.get_path(), file)):
                    if not test_mode:
                        copied_path = shutil.copy(os.path.join(source_path, file), folder.get_path())
                        LOGGER.info(f"Copied '{file}' to '{copied_path}'")
                    else:
                        LOGGER.info(f"Copied '{file}' to '{folder.name}' (test mode)")
                    return True
                else:
                    LOGGER.debug(f"File '{file}' is already sorted in '{folder.name}', nothing to do")
                    return False
    else:
        LOGGER.error(f"No date found for '{file}', can't sort it")
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
    config = Config()

    # Pushbullet auth
    pushbullet_conn = None
    if config.pushbullet_api_key is not None or config.pushbullet_api_key != "":
        pushbullet_conn = Pushbullet(config.pushbullet_api_key, config.pushbullet_encryption_key)

    # Fix paths in case user and dev are dumbasses
    if not config.source_path.endswith('/'):
        config.source_path += '/'
    for path in config.storage_paths:
        if not path.endswith('/'):
            config.storage_paths[config.storage_paths.index(path)] += '/'

    # Read folders and sort files
    count = 0
    sorted_count = 0
    unsortable_count = 0
    dir_list = list_folders(config.storage_paths, config.storage_ignore)
    if len(dir_list) > 0:
        for name in os.listdir(config.source_path):
            count += 1
            if os.path.isfile(f"{config.source_path}{name}") and name not in config.source_ignore:
                if name.endswith(".mp4"):
                    if sort_file(config.source_path, name,
                                 get_vid_meta_date(config.source_path, name, config.data_keys), dir_list,
                                 config.test_mode):
                        sorted_count += 1
                elif name.endswith(".jpg"):
                    if sort_file(config.source_path, name,
                                 get_pic_meta_date(config.source_path, name, config.data_keys), dir_list,
                                 config.test_mode):
                        sorted_count += 1
                else:
                    unsortable_count += 1
                    LOGGER.error(f"Unsortable file '{name}'")
    else:
        LOGGER.error("No storage directories found")
    if pushbullet_conn:
        pushbullet_conn.push_note(f"{socket.gethostname()} - PhotoSort executed",
                                  f"{sorted_count} of {count} files sorted, {unsortable_count} unsortables files")
    LOGGER.info(f"Execution end at {datetime.now()}")


# MAIN
if __name__ == '__main__':
    sys.path.append("/var/packages/MediaServer/target/bin/ffmpeg")
    sys.path.append("/var/packages/MediaServer/target/bin/ffprobe")
    main()
