from   dronekit           import connect, VehicleMode, LocationGlobalRelative, APIException
from   picamera2          import Picamera2
from   picamera2.encoders import H264Encoder, Quality
from   pymavlink          import mavutil
from   time               import sleep
from   datetime           import datetime, timedelta
from   cv2                import aruco
from   missions           import arm_and_takeoff
from   initialize         import initialize
from   aruco_detector     import ArUcoDetector
from   irc_bot_utils      import IRCBot, UAVBot, UGVHitListener, run_bot
import numpy              as np
import time
import cv2
import logging
import irc.client
import irc.bot
import threading

###################################################################################
# This file requires the mission to have a return to launch/landing waypoint
###################################################################################

# Initializing PiCamera2 object with main preview configuration set to XRGB8888 format and 640x480 resolution
picam2.configure(picam2.create_preview_configuration(main = {"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

print("Creating the IRC bots...")

# Create and start the UAVBot in a separate thread
uav_bot    = UAVBot()
uav_thread = threading.Thread(target = run_bot, args = (uav_bot,))
uav_thread.start()

# Create and start the UGVHitListener in a separate thread
listener        = UGVHitListener()
listener_thread = threading.Thread(target = run_bot, args = (listener,))
listener_thread.start()

# Wait for the UAVBot and UGVHitListener to connect to the server
while not uav_bot.connected and not listener.connected:
    time.sleep(1)

vehicle, aruco_detector = initialize()

# Aruco
while True:
    frame = picam2.capture_array()
    
    aruco_detector.detect_markers(frame)
    
    corners, ids = aruco_detector.detect_markers(frame)
    aruco_detector.draw_markers(frame, corners, ids)
            
    
                
    #cv2.imshow("Camera", frame)
    #key = cv2.waitKey(25)
    
    """
    if key == ord("q"):
        break
    """

file.write("============== END LOG ==============\n\n")
file.close()

vehicle.close()
#picam2.stop_recording()
#cv2.destroyAllWindows()
exit()
