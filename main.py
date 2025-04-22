import socket
import sys
import logging
import os
from datetime import datetime
from typing import List

import loging_config  # noqa: F401

from config import Config, SourceConfig
from dated_folder import DatedFolder

from file import File
from notification.notifier import Notifier

LOGGER = logging.getLogger(__name__)


def sort_source(source: SourceConfig, dir_list: List[DatedFolder], count: int, sorted_count: int, unsortable_count: int):
    """
    Sort files from a given source
    :param source: Files source configuration of files to sort
    :param dir_list: List of dated folders to sort into
    :return: counters packed in a tuple
    """
    count = 0
    sorted_count = 0
    unsortable_count = 0

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

    notifier = Notifier()

    # Read folders and sort files
    total_count = 0
    total_sorted_count = 0
    total_unsortable_count = 0
    sources_reports = []
    dir_list = DatedFolder.list_folders(
        private_paths=Config.private_storage_paths,
        public_paths=Config.public_storage_paths,
        ignore=Config.storage_ignore
    )
    if len(dir_list) > 0:
        for source in Config.sources:
            if source.source_path is not None:
                LOGGER.info(f"Sorting source {source.name}")
                count, sorted_count, unsortable_count = sort_source(source=source,
                                                                    dir_list=dir_list,
                                                                    count=total_count,
                                                                    sorted_count=total_sorted_count,
                                                                    unsortable_count=total_unsortable_count,
                                                                    )
                total_count += count
                total_sorted_count += sorted_count
                total_unsortable_count += unsortable_count
                source_report = f"{source.name} - {sorted_count}/{count}, unsortables {unsortable_count}"
                sources_reports.append(source_report)
                LOGGER.info(f"Sorted source {source_report}")
    else:
        LOGGER.error("No storage directories found")

    sources_reports.insert(0, f"{total_sorted_count} of {total_count} files sorted, {total_unsortable_count} unsortables files")
    execution_report = "\n".join(sources_reports)

    notifier.notify(f"{socket.gethostname()} - {Config.username} - PhotoSort executed", execution_report)
    LOGGER.info(execution_report)
    LOGGER.info(f"Execution end at {datetime.now()}")


# MAIN
if __name__ == '__main__':
    sys.path.append("/var/packages/MediaServer/target/bin/ffmpeg")
    sys.path.append("/var/packages/MediaServer/target/bin/ffprobe")
    logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.INFO)
    logging.getLogger("PIL.TiffImagePlugin").propagate = False
    main()
