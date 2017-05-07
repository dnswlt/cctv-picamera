#!/usr/bin/env python3

from picamera import PiCamera
from datetime import datetime
import numpy as np
import sys
from time import sleep


max_res = (3280, 2464)
hd_res = (1920, 1080)
cctv_res = (640, 360)

def np_shape(resolution):
  """Convert resolution (width, height) to (norm(height), norm(width), 3) for numpy."""
  width, height = resolution
  if width % 32 > 0:
    width += 32 - width % 32
  if height % 16 > 0:
    height += 16 - height % 16
  return (height, width, 3)

def snap():
  """Take a snapshot, save as .jpg"""
  with PiCamera() as cam:
    sleep(2)
    cam.resolution = max_res
    cam.capture('snap_{}.jpg'.format(datetime.now().strftime("%Y%m%d%H%M%S")))

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


def calibrate(cam, n=20, resolution=cctv_res):
  prev = None
  ds = []
  res = resolution
  for i in range(n):
    img = np.empty(np_shape(res), dtype=np.uint8) # sic!
    cam.capture(img, 'rgb', resize=res, use_video_port=True)
    img = img[:res[1], :res[0], :]
    if prev is not None:
      d = np.fabs(img.astype('int16') - prev.astype('int16'))
      ds.append(np.mean(d*d))
    prev = img
    sleep(1)
  ds = np.array(ds) 
  return (np.min(ds), np.mean(ds), np.max(ds))

# http://picamera.readthedocs.io/en/release-1.13/recipes1.html
def mon(n=30):
  """Monitor images, outputting mean differences in measured pixels.
  `n` specifies how many iterations to run. Set it to -1 if you want
  to run forever.
  """
  with PiCamera(resolution=hd_res, framerate=30) as cam:
    #cam.resolution = (1024, 768) # 3280 × 2464
    shutter_speed, awb_gains = fix_camera_settings(cam)
    print("Set shutter speed to {}, AWB gains to {}".format(shutter_speed, awb_gains))
    prev = None
    res = cctv_res
    min_dev, mean_dev, max_dev = calibrate(cam, n=20, resolution=res)
    if mean_dev > 5:
      print("Warning: mean deviation is above 5 (at {:.2f})".format(mean_dev))
    if max_dev > 10:
      print("Warning: max deviation during calibration was above 10 (at {:.2f})".format(max_dev))
    max_dev *= 1.3
    print("Using max deviation of {:.2f}".format(max_dev))
    for i in range(n if n != -1 else 2**64):
      img = np.empty(np_shape(res), dtype=np.uint8) # sic!
      cam.capture(img, 'rgb', resize=res, use_video_port=True)
      img = img[:res[1], :res[0], :]
      if prev is not None:
        d = np.fabs(img.astype('int16') - prev.astype('int16'))
        sqdev = np.mean(d*d)
        if sqdev > max_dev:
          print("{}: Motion detected! Taking pictures".format(datetime.now()))
          files = record_seq(cam, num_images=3)
          if files:
            print("Files saved to\n{}".format("\n".join(files)))
          else:
            print("Warning: no files could be saved.")
          prev = None
        else:
          prev = img
      else:
        prev = img
      sleep(2)

def main():
  m = sys.argv[1]
  if m in globals():
    globals()[m]()
  else: 
    print("Kann ich nicht") 

if __name__ == "__main__":
  main()

