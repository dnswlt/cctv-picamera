#!/usr/bin/env python3

"""CCTV video recording with the Raspberry Pi camera.
"""

import numpy as np
from picamera import PiCamera
import picamera.array
from time import sleep
import time
import argparse
import re


class CctvMotionAnalysis(picamera.array.PiMotionAnalysis):
    def __init__(self, *args, **kwargs):
        picamera.array.PiMotionAnalysis.__init__(self, *args, **kwargs)
        self.motion_detected = 0

    def analyse(self, a):
        a = np.sqrt(
                np.square(a['x'].astype(np.float)) + 
                np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
        print(np.histogram(a, range=(0, 255))[0]) # > 40).sum())
        if (a > 40).sum() > 10:
            self.motion_detected += 1
            # print(self.motion_detected)


def detect():
    with PiCamera(resolution=(640,480), framerate=25) as cam:
        with CctvMotionAnalysis(cam) as output:
            cam.start_recording('/dev/null', motion_output=output, format='h264')
            cam.wait_recording(60)
            cam.stop_recording()


def cctv(out_file="cctv-{timestamp}.h264", duration=10, resolution=(640, 480), framerate=25):
    """Record video to out_file for dur seconds.
    
    out_file may contain a placeholder `{timestamp}` which will be replaced by the 
    start date/time of the recording.
    """
    cam = PiCamera(resolution=resolution, framerate=framerate)
    out_file = out_file.replace("{timestamp}", time.strftime("%Y%m%d-%H%M%S"))
    print("Recording to {out_file} at resolution {width}x{height} and framerate {fps}".format(out_file=out_file, width=resolution[0], height=resolution[1], fps=cam.framerate))
    cam.start_recording(out_file)
    cam.wait_recording(duration)
    cam.stop_recording()
    

def arg_resolution(s):
    """Parse NxM resolution cmdline argument, and return it as a tuple."""
    mo = re.match(r'(\d+)x(\d+)', s)
    if mo is None: 
        raise argparse.ArgumentTypeError("Not a valid resolution: " + s)
    return (int(mo.group(1)), int(mo.group(2)))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="CCTV homebrew")
    p.add_argument('--resolution', '-r', metavar="WxH", default='640x480', type=arg_resolution, help="Video resolution {Width}x{Height}")
    p.add_argument('--dur', '-d', metavar="S", default=10, type=int, help="Recording duration in seconds")
    args = p.parse_args()
    # cctv(resolution=args.resolution, dur=args.dur)
    detect()

