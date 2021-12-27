import os
import sys
from datetime import datetime
from pprint import pprint

import ffmpeg
ffmpeg_install = "/var/packages/MediaServer/target/bin/ffmpeg"
ffprobe_install = "/var/packages/MediaServer/target/bin/ffprobe"
ffmpeg_bin = "/usr/bin/ffmpeg"

# sys.path.append(ffmpeg_install)
# sys.path.append(ffprobe_install)

# os.environ["PATH"] += os.pathsep + ffmpeg_install
# os.environ["PATH"] += os.pathsep + ffprobe_install
os.environ["PATH"] += os.pathsep + ffmpeg_bin

name = "VID_20200130_185053.mp4"
# name = "VID_20191207_234942.mp4"
path = "/volume1/photo/phone/DCIM/Camera/"
# path = "/home/junn/sample/"
data_keys = ["DateTimeOriginal", "DateTime", "creation_time"]
#
file = f"{path}{name}"
print(file)
vid = ffmpeg.probe(file)['streams']
# vid = ffprobe.FFProbe(file).streams
for key in data_keys:
    if key in vid[0]['tags']:
        print(datetime.strptime(vid[0]['tags'].get(key).split('T')[0], "%Y-%m-%d"))
