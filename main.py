import socket
import sys
import logging
import os
from datetime import datetime
import loging_config  # noqa: F401

from config import Config
from dated_folder import DatedFolder
from pushbullet import Pushbullet

from file import File

LOGGER = logging.getLogger(__name__)


def main():
    config = Config()
    File.data_keys = config.data_keys

    # Pushbullet auth
    pushbullet_conn = None
    if config.pushbullet_api_key:
        pushbullet_conn = Pushbullet(config.pushbullet_api_key, config.pushbullet_encryption_key)

    # Read folders and sort files
    count = 0
    sorted_count = 0
    unsortable_count = 0
    dir_list = DatedFolder.list_folders(config.storage_paths, config.storage_ignore)
    if len(dir_list) > 0:
        for name in os.listdir(config.source_path):
            count += 1
            if (config.source_path/name).is_file() and name not in config.source_ignore:
                file = File.get_type(filename=name, dir_path=config.source_path)
                if file and file.is_sortable:
                    sort_result = file.sort(storage_paths=dir_list, test_mode=config.test_mode)
                    if sort_result:
                        sorted_count += 1
                        continue
                unsortable_count += 1
                LOGGER.error(f"Unsortable file '{name}'")
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
