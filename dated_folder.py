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
        date = self.name.split(" ")[0]
        try:
            # One day folder
            if len(date) == 10:
                self.begin = date_time.strptime(date, "%Y-%m-%d")
                self.end = self.begin

            # One month folder
            elif len(date) == 7:
                self.begin = date_time.strptime(date, "%Y-%m")
                self.end = last_day_of_month(self.begin)

            # One year folder
            elif len(date) == 4:
                self.isValid = False
                # self.begin = date_time.strptime(date, "%Y")
                # self.end = self.begin.replace(month=12, day=31)

            # Interval folder
            elif ".." in date:
                dates = date.split("..")

                # Month only date with interval
                if len(dates[0]) == 7 and len(dates[1]) == 2:
                    self.begin = date_time.strptime(dates[0], "%Y-%m")
                    self.end = last_day_of_month(self.begin.replace(month=int(dates[1])))

                # Full date with same month interval
                elif len(dates[0]) == 10 and len(dates[1]) == 2:
                    self.begin = date_time.strptime(dates[0], "%Y-%m-%d")
                    self.end = self.begin.replace(day=int(dates[1]))

                # Full date with different month interval
                elif len(dates[0]) == 10 and len(dates[1]) == 5:
                    month, day = dates[1].split('-')
                    self.begin = date_time.strptime(dates[0], "%Y-%m-%d")
                    self.end = self.begin.replace(month=int(month), day=int(day))

                # Two full dates
                elif len(dates[0]) == 10 and len(dates[1]) == 10:
                    self.begin = date_time.strptime(dates[0], "%Y-%m-%d")
                    self.end = date_time.strptime(dates[1], "%Y-%m-%d")

                else:
                    LOGGER.error(f"Folder name '{self.name}' is invalid")
                    self.isValid = False

            # Multiple days of the same month folder
            elif '.' in date:
                dates = date.split(".")
                if len(dates[0]) == 10:
                    self.begin = date_time.strptime(dates[0], "%Y-%m-%d")
                    self.end = self.begin.replace(day=int(dates[len(dates) - 1]))
                else:
                    LOGGER.error(f"Folder name '{self.name}' is invalid")
                    self.isValid = False

            else:
                LOGGER.error(f"Folder name '{self.name}' is invalid '{date}'")
                self.isValid = False
        except ValueError as e:
            LOGGER.error(f"Folder name '{self.name}' is invalid : {e}")
            self.isValid = False

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
