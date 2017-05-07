#!/usr/bin/env python3

from picamera import PiCamera
from datetime import datetime
import numpy as np
import sys
from time import sleep

def series():
  """Shoot a series of images as .jpg files."""
  with PiCamera() as cam:
    cam.resolution = (1024, 768)
    for i in range(10):
      cam.capture('series_{:02d}.jpg'.format(i))

def info():
  """Print values of all PiCamera attributes to stdout."""
  with PiCamera() as cam:
    for f in sorted(dir(cam)):
      if f.startswith("_"):
        continue
      try:
        print("{}: {}".format(f, getattr(cam, f)))
      except:
        print("{} inaccessible".format(f))

def fix_camera_settings(cam):
  """Calibrate camera:
  - ISO 100
  - Shutter speed and AWB gains as camera automatic control chooses for current scene
  - Exposure and AWB mode set to 'off'
  Returns chosen (shutter_speed, awb_gains)
  """
  cam.iso = 100
  sleep(2) # wait for automatic control to settle
  e = cam.exposure_speed
  cam.shutter_speed = e
  cam.exposure_mode = 'off'
  g = cam.awb_gains
  cam.awb_mode = 'off'
  cam.awb_gains = g
  return (e, g)


max_sq_dev = 3.0

def record_seq(cam, num_images=10, pause_millis=1000):
  """Record a sequence of `num_images` JPEG images. 
  Return list of filenames."""
  result = []
  for i in range(num_images):
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = 'seq_{}_{}.jpg'.format(now, i)
    try:
      cam.capture(filename, use_video_port=False)
      result.append(filename)
      sleep(pause_millis/1000.0)
    except Exception as e:
      print("Some bad shit happened: {}".format(e))
  return result


def calibrate(n=30):
  with PiCamera(resolution=(1920, 1080), framerate=30) as cam:
    #cam.resolution = (1024, 768) # 3280 × 2464
    shutter_speed, awb_gains = fix_camera_settings(cam)
    print("Set shutter speed to {}, AWB gains to {}".format(shutter_speed, awb_gains))
    prev = None
    ds = []
    for i in range(n):
      img = np.empty((368, 640, 3), dtype=np.uint8) # sic!
      cam.capture(img, 'rgb', resize=(640, 360), use_video_port=True)
      img = img[:360, :, :]
      if prev is not None:
        d = np.fabs(img.astype('int16') - prev.astype('int16'))
        ds.append(np.mean(d*d))
      prev = img
      sleep(1)
    ds = np.array(ds) 
    print(ds)
    print(np.min(ds), np.median(ds), np.mean(ds), np.max(ds), np.std(ds))
    print((ds - np.mean(ds)) / np.std(ds))

# http://picamera.readthedocs.io/en/release-1.13/recipes1.html
def mon(n=30):
  """Monitor images, outputting mean differences in measured pixels.
  `n` specifies how many iterations to run. Set it to -1 if you want
  to run forever.
  """
  with PiCamera(resolution=(1920, 1080), framerate=30) as cam:
    #cam.resolution = (1024, 768) # 3280 × 2464
    shutter_speed, awb_gains = fix_camera_settings(cam)
    print("Set shutter speed to {}, AWB gains to {}".format(shutter_speed, awb_gains))
    prev = None
    for i in range(n if n != -1 else 2**64):
      img = np.empty((360, 640, 3), dtype=np.uint8) # sic!
      cam.capture(img, 'rgb', resize=(640, 360), use_video_port=True)
      if prev is not None:
        d = np.fabs(img.astype('int16') - prev.astype('int16'))
        sqdev = np.mean(d*d)
        if sqdev > max_sq_dev:
          record_seq(cam)
          prev = None
        else:
          prev = img
          sleep(1)

def main():
  m = sys.argv[1]
  if m in globals():
    globals()[m]()
  else: 
    print("Kann ich nicht") 

if __name__ == "__main__":
  main()

