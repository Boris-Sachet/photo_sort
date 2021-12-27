from datetime import datetime

import ffmpeg

name = "VID_20200130_185053.mp4"
path = "/volume1/photo/phone/DCIM/Camera"
data_keys = ["DateTimeOriginal", "DateTime", "creation_time"]

file = f"{path}{name}"
vid = ffmpeg.probe(file)['streams']
# vid = ffprobe.FFProbe(file).streams
for key in data_keys:
    if key in vid[0]['tags']:
        print(datetime.strptime(vid[0]['tags'].get(key).split('T')[0], "%Y-%m-%d"))
else:
    print("Nothing found")