import datetime
import logging
import os
import os.path
from datetime import datetime as date_time
from pathlib import Path
from typing import List

from config import Config

LOGGER = logging.getLogger(__name__)


def last_day_of_month(any_day):
    # this will never fail
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month,
    # or said programmatically said, the previous day of the first of next month
    return next_month - datetime.timedelta(days=next_month.day)


class DatedFolder:

    def __init__(self, name: str, path: Path, is_public: bool):
        self.name = name
        self.path = path / name
        self.begin = date_time.now()
        self.end = self.begin
        self.isValid = True
        self.is_public = is_public
        self.extract_dates()
        self.end = self.end.replace(hour=23, minute=59, second=59)

    def extract_dates(self):
        """Extract begin and end dates from the folder name"""
        date = self.normalise_folder_name().split(" ")[0]
        try:
            # Multiple days interval folder
            if ".." not in date:
                self.begin = self.parse_begin_date(date)
                self.end = self.begin
            else:
                splited_date = date.split("..")
                self.begin = self.parse_begin_date(splited_date[0])
                self.end = self.parse_end_date(splited_date[1])

        except ValueError as e:
            LOGGER.error(f"Folder name '{self.name}' is invalid : {e}")
            self.isValid = False

    def normalise_folder_name(self) -> str:
        """Normalise folder name for better parsing of dates"""
        match self.name.split(" ")[1].lower():
            case "et":
                normalised_name = self.name.replace("et", "..", 1)
            case "au":
                normalised_name = self.name.replace("au", "..", 1)
            case "à":
                normalised_name = self.name.replace("à", "..", 1)
            case _:
                normalised_name = self.name
        return normalised_name

    def parse_begin_date(self, date: str) -> datetime:
        """Looks for accepted date format in strings"""
        match len(date):
            case 10:
                return date_time.strptime(date, "%Y-%m-%d")
            case 8:
                return date_time.strptime(date, "%Y%m%d")

    def parse_end_date(self, date: str) -> datetime:
        """looks for accepted date format in second strings"""
        match len(date):
            # YYYY-MM-DD
            case 10:
                return date_time.strptime(date, "%Y-%m-%d")
            # YYYMMDD
            case 8:
                return date_time.strptime(date, "%Y%m%d")
            # MM-DD
            case 5:
                month, day = date.split('-')
                return self.begin.replace(month=int(month), day=int(day))
            # MMDD
            case 4:
                return self.begin.replace(month=int(date[:2]), day=int(date[2:]))
            # DD
            case 2:
                return self.begin.replace(day=int(date))
            # D
            case 1:
                return self.begin.replace(day=int(date))

    def find_user_subfolder(self) -> Path:
        """Look for a user subfolder in this folder"""
        for subfolder in os.listdir(self.path):
            if (self.path / subfolder).is_dir() and subfolder.lower() in Config.public_storages_subdir_names:
                return self.path / subfolder

    def __str__(self):
        return f"{self.name} - {self.begin} - {self.end}"

    @staticmethod
    def list_folders(private_paths: List[Path], public_paths: List[Path], ignore: List[str]) -> list:
        """
        List all storage folders in given paths and create a list of dated_folder objects with every valid data folder
         found Data folder is valid only if it starts with a date that this scrip can read
        :param public_paths: List of public paths in which to look for storage folder
        :param private_paths: List of private paths in which to look for storage folder
        :param ignore: list of folder names to ignore
        :return: List of dated_folder object containing the info of every valid folder found
        """
        results = []
        # Private paths listing
        for path in private_paths:
            for name in os.listdir(path):
                if (path / name).is_dir() and name not in ignore:
                    result = DatedFolder(name, path, False)
                    if result.isValid:
                        results.append(result)
        # Public paths listing
        for path in public_paths:
            for name in os.listdir(path):
                if (path / name).is_dir() and name not in ignore:
                    result = DatedFolder(name, path, True)
                    if result.isValid:
                        results.append(result)
        LOGGER.info(f"{len(results)} storage folder found")
        return results
