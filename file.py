import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

import ffmpeg
from PIL import Image, ExifTags

from dated_folder import DatedFolder

LOGGER = logging.getLogger(__name__)


class File:
    data_keys = []

    def __init__(self, filename: str, dir_path: Path):
        self.filename = filename
        self.dir_path = dir_path
        self.path = self.dir_path / self.filename
        self.date = None
        self.is_sortable = False

    def get_date_from_name(self) -> datetime | None:
        """Attempt to get the file creation date from its name"""
        for string in self.filename.split('_'):
            if len(string) == 8:
                try:
                    result = datetime.strptime(string, "%Y%m%d")
                    return result
                except ValueError:
                    LOGGER.debug(f"{self.filename} : Can't convert '{string}' to datetime")
        LOGGER.error(f"{self.filename} : No date found in filename")
        return None

    def sort(self, storage_paths: List[DatedFolder], test_mode: bool) -> bool:
        """Sort the file in the correct folder"""
        if self.date is not None:
            for folder in storage_paths:
                if folder.begin <= self.date <= folder.end:
                    if not (folder.path / self.filename).is_file():
                        if not test_mode:
                            copied_path = shutil.copy(self.path, folder.path)
                            LOGGER.info(f"Copied '{self.filename}' to '{copied_path}'")
                        else:
                            LOGGER.info(f"Copied '{self.filename}' to '{folder.name}' (test mode)")
                        return True
                    else:
                        LOGGER.debug(f"File '{self.filename}' is already sorted in '{folder.name}', nothing to do")
                        return False
        else:
            LOGGER.error(f"No date found for '{self.filename}', can't sort it")
            return False

    @classmethod
    def get_type(cls, filename: str, dir_path: Path):
        """
        Determine if file is a photo or a video and return the proper object
        :param filename: name of the file
        :param dir_path: path containing the file
        :return: Instance of file subclass
        """
        if filename.endswith(".mp4"):
            return Video(filename, dir_path)
        elif filename.endswith(".jpg"):
            return Photo(filename, dir_path)


class Photo(File):
    def __init__(self, filename: str, dir_path: Path):
        super().__init__(filename, dir_path)
        self.is_sortable = True
        self.date = self.get_date_from_metadata()

    def get_date_from_metadata(self) -> datetime | None:
        """Attempt to get the photo creation date from metadata"""
        # Can also be done with:
        # import exifread
        # f = open(file, 'rb')
        # tags = exifread.process_file(f)
        try:
            img = Image.open(self.path)
            exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}
            for key in self.data_keys:
                if key in exif.keys():
                    return datetime.strptime(exif.get(key).split(' ')[0], "%Y:%m:%d")
        except Exception as error:
            file_date = self.get_date_from_name()
            if file_date is None:
                LOGGER.error(f"{self.filename} metadata reading : {error}")
            else:
                return file_date
        return None


class Video(File):
    def __init__(self, filename: str, dir_path: Path):
        super().__init__(filename, dir_path)
        self.is_sortable = True
        self.date = self.get_date_from_metadata()

    def get_date_from_metadata(self) -> datetime | None:
        """Attempt to get the video creation date from metadata"""
        try:
            vid = ffmpeg.probe(self.path)['streams']
            for key in self.data_keys:
                if key in vid[0]['tags']:
                    return datetime.strptime(vid[0]['tags'].get(key).split('T')[0], "%Y-%m-%d")
        except ffmpeg.Error as e:
            LOGGER.error(f"{self.filename} metadata reading : {e.stderr}")
        except Exception as e:
            LOGGER.error(f"{self.filename} metadata reading : {e}")
        return self.get_date_from_name()
