import socket
import sys
import logging
import os
from datetime import datetime
from typing import List

import loging_config  # noqa: F401

from config import Config, SourceConfig
from dated_folder import DatedFolder
from pushbullet import Pushbullet

from file import File

LOGGER = logging.getLogger(__name__)


def sort_source(source: SourceConfig, dir_list: List[DatedFolder], count: int, sorted_count: int, unsortable_count: int):
    """
    Sort files from a given source
    :param source: Files source configuration of files to sort
    :param dir_list: List of dated folders to sort into
    :param count: Total count of files treated
    :param sorted_count: Total count of files sorted
    :param unsortable_count: Total count of files unsorted
    :return: counters packed in a tuple
    """
    for name in os.listdir(source.source_path):
        count += 1
        if (source.source_path / name).is_file() and name not in source.source_ignore:
            file = File.get_type(filename=name, dir_path=source.source_path)
            if file and file.is_sortable:
                sort_result = file.sort(storage_paths=dir_list, source=source)
                if sort_result:
                    sorted_count += 1
                    continue
            else:
                unsortable_count += 1
                LOGGER.error(f"Unsortable file '{name}'")

    return count, sorted_count, unsortable_count


def main():
    Config.init()
    File.data_keys = Config.data_keys

    # Pushbullet auth
    pushbullet_conn = None
    if Config.pushbullet_api_key:
        pushbullet_conn = Pushbullet(Config.pushbullet_api_key, Config.pushbullet_encryption_key)

    # Read folders and sort files
    count = 0
    sorted_count = 0
    unsortable_count = 0
    dir_list = DatedFolder.list_folders(
        private_paths=Config.private_storage_paths,
        public_paths=Config.public_storage_paths,
        ignore=Config.storage_ignore
    )
    if len(dir_list) > 0:
        for source in Config.sources:
            if source.source_path is not None:
                count, sorted_count, unsortable_count = sort_source(source=source,
                                                                    dir_list=dir_list,
                                                                    count=count,
                                                                    sorted_count=sorted_count,
                                                                    unsortable_count=unsortable_count,
                                                                    )
                LOGGER.info(f"Sorted source {source.name}")
    else:
        LOGGER.error("No storage directories found")

    execution_report = f"{sorted_count} of {count} files sorted, {unsortable_count} unsortables files"
    if pushbullet_conn:
        pushbullet_conn.push_note(f"{socket.gethostname()} - PhotoSort executed", execution_report)
    LOGGER.info(execution_report)
    LOGGER.info(f"Execution end at {datetime.now()}")


# MAIN
if __name__ == '__main__':
    sys.path.append("/var/packages/MediaServer/target/bin/ffmpeg")
    sys.path.append("/var/packages/MediaServer/target/bin/ffprobe")
    main()
