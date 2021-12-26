import os
from datetime import datetime

from PIL import Image, ExifTags
# from pprint import pprint
import ffmpeg

from dated_folder import DatedFolder


def get_pic_meta_date(path: str, name: str, data_keys: list) -> datetime:
    img = Image.open(f"{path}{name}")
    exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}
    for key in data_keys:
        if key in exif.keys():
            return datetime.strptime(exif.get(key).split(' ')[0], "%Y:%m:%d")
    else:
        return None


def get_vid_meta_date(path: str, name: str, data_keys: list) -> datetime:
    file = f"{path}{name}"
    try:
        vid = ffmpeg.probe(file)['streams']
        for key in data_keys:
            if key in vid[0]['tags']:
                return datetime.strptime(vid[0]['tags'].get(key).split('T')[0], "%Y-%m-%d")
        else:
            return None
    except ffmpeg.Error as e:
        print(e.stderr)


def list_folders(paths: list, ignore: list) -> list:
    results = []
    for path in paths:
        for name in os.listdir(path):
            if os.path.isdir(f"{path}{name}") and name.lower() not in ignore:
                result = DatedFolder(name, path)
                if result.isValid:
                    results.append(result)
    return results


def sort_file(source_path: str, file: str, date: datetime, storage_paths: list):
    if date is not None:
        for path in storage_paths:
            if path.begin <= date <= path.end:
                if not os.path.isfile(f"{source_path}"):
                    print(f"Moving '{file}' to '{str(path)}'")
                    return
                else:
                    return


def main():
    data_keys = ["DateTimeOriginal", "DateTime", "creation_time"]
    source_path = "/home/junn/sample/"
    # if not source_path.endswith('/'):
    #     source_path += '/'
    source_ignore = []
    storage_paths = ["/home/junn/sample/"]
    storage_ignore = []
    dir_list = list_folders(storage_paths, storage_ignore)

    # for item in dir_list:
    #     print(str(item))
    # print()
    # print()

    for name in os.listdir(source_path):
        if os.path.isfile(f"{source_path}{name}") and name.lower() not in source_ignore:
            if name.endswith(".mp4"):
                # print(f"{name} : {get_vid_meta_date(source_path, name, data_keys)}")
                sort_file(source_path, name, get_vid_meta_date(source_path, name, data_keys), dir_list)
            elif name.endswith(".jpg"):
                # print(f"{name} : {get_pic_meta_date(source_path, name, data_keys)}")
                sort_file(source_path, name, get_pic_meta_date(source_path, name, data_keys), dir_list)
            else:
                print(f"ERROR: Unsortable file '{name}'")


# MAIN
if __name__ == '__main__':
    main()
