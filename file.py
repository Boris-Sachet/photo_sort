import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

import ffmpeg
from PIL import Image, ExifTags

from config import Config, SourceConfig
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

    def sort(self, storage_paths: List[DatedFolder], source: SourceConfig) -> bool:
        """Sort the file in the correct folder"""
        # Find the dated folder matching this file date
        folder = self.__find_folder_to_sort_into(storage_paths)
        if folder is None:
            return False

        # Find storage path for file in current folder
        storage_path = self.__find_storage_path(folder, source)
        if storage_path is None:
            LOGGER.debug(f"No correct subfolder for {self.filename} in {folder.name}")
            return False

        # If correct storage path if found, copy the file if it doesn't exist already (unless test mode)
        if not (storage_path / self.filename).is_file():
            self.copy(dst=storage_path)
            return True

        # File is already there, nothing to do
        LOGGER.debug(f"File '{self.filename}' is already sorted in '{folder.name}', nothing to do")
        return False

    def copy(self, dst: Path):
        """
        Copy the file to destination folder.
        If test mode is not enabled (else pretend to do it in the logs)
        :param dst:
        :return:
        """
        if not Config.test_mode:
            copied_path = shutil.copy(self.path, dst)
            LOGGER.info(f"Copied '{self.filename}' to '{copied_path}'")
        else:
            LOGGER.info(f"Copied '{self.filename}' to '{dst}' (test mode)")

    def __find_folder_to_sort_into(self, storage_paths: List[DatedFolder]) -> DatedFolder:
        """Find the dated folder with the date interval matching the date of this file"""
        if self.date is not None:
            for folder in storage_paths:
                # Search the folder matching the date of the file (only first one found counts)
                if folder.begin <= self.date <= folder.end:
                    return folder
        else:
            LOGGER.error(f"No date found for '{self.filename}', can't sort it")

    @classmethod
    def __find_storage_path(cls, folder: DatedFolder, source: SourceConfig) -> Path | None:
        """Find the correct storage path for the file in the given folder"""
        # User folder handling
        if not folder.is_public:
            user_storage_path = folder.path
        else:
            user_storage_path = folder.find_user_subfolder()
        # Don't bother searching for source subfolder if user folder is required but missing
        if user_storage_path is None:
            return user_storage_path

        # Source subfolder handling
        # Return folder path or folder user path if source doesn't use subdir
        if not source.use_subdir:
            return user_storage_path
        # If source require subdir look for it in folder path or folder user path
        for subfolder in os.listdir(user_storage_path):
            if (user_storage_path / subfolder).is_dir() and subfolder.lower() in source.subdir_names:
                return user_storage_path / subfolder
        # If no source subdir found return nothing so file has nowhere to go
        return None

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
