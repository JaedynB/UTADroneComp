from   dronekit  import connect, VehicleMode, LocationGlobalRelative, APIException
from   picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
import time
from time import sleep
from datetime import datetime, timedelta
import cv2
from cv2 import aruco
import numpy     as np


connection_string = '/dev/ttyUSB0'
print('Connecting to vehicle on: ', connection_string)
vehicle = connect(connection_string,baud=57600,wait_ready=True)
print('Connected')

print("Starting mission")
if vehicle.mode != 'STABILIZE':
    vehicle.wait_for_mode('STABILIZE')
    print('Mode: ', vehicle.mode)
    
print('Arming...')
vehicle.arm()
if vehicle.armed == True:
    print('Armed')
else:
    print('Could not arm...')
###########################################
picam2 = Picamera2()
#picam2.configure(picam2.create_video_configuration())

picam2.resolution = (640, 480)
picam2.start_and_record_video("test.mp4", duration = 30)


#encoder = H264Encoder()
#output = "test.h264"
#picam2.start_recording(encoder, 'test.h264', Quality.HIGH)

time.sleep(30)
picam2.stop_recording()
#################################################

exit()
