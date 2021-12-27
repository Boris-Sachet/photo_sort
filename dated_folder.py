import datetime
import os.path
from datetime import datetime as date_time


def last_day_of_month(any_day):
    # this will never fail
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month,
    # or said programmatically said, the previous day of the first of next month
    return next_month - datetime.timedelta(days=next_month.day)


class DatedFolder:

    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path if path.endswith('/') else path + '/'
        self.desc = name.split(' ', 1)[1] if len(name.split(' ', 1)[1]) == 2 else ""
        self.begin = date_time.now()
        self.end = self.begin
        self.isValid = True
        self.extract_dates()
        self.end = self.end.replace(hour=23, minute=59, second=59)

    def extract_dates(self):
        date = self.name.split(" ")[0]

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
            self.begin = date_time.strptime(date, "%Y")
            self.end = self.begin.replace(month=12, day=31)

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
                print(f"ERROR: Folder name '{self.name}' is invalid")
                self.isValid = False

        # Multiple days of the same month folder
        elif '.' in date:
            dates = date.split(".")
            if len(dates[0]) == 10:
                self.begin = date_time.strptime(dates[0], "%Y-%m-%d")
                self.end = self.begin.replace(day=int(dates[len(dates) - 1]))
            else:
                print(f"ERROR: Folder name '{self.name}' is invalid")
                self.isValid = False

        else:
            print(f"ERROR: Folder name '{self.name}' is invalid")
            self.isValid = False

    def __str__(self):
        return f"{self.name} - {self.begin} - {self.end}"

    def get_path(self) -> str:
        return os.path.join(self.path, self.name)
