from   dronekit           import connect, VehicleMode, LocationGlobalRelative, APIException
import collections
from   picamera2          import Picamera2
from   picamera2.encoders import H264Encoder, Quality
from   pymavlink          import mavutil
from   time               import sleep
from   datetime           import datetime, timedelta
from   cv2                import aruco
import numpy              as     np
import time
import cv2
import logging
import irc.client
import irc.bot
import threading
import datetime

connection_string = '/dev/ttyUSB0'

print('Connecting to vehicle on: ', connection_string)
vehicle = connect(connection_string,baud = 57600,wait_ready = True)
print('Connected')


"""
print('Arming...')
vehicle.arm()


if vehicle.armed == True:
    print('Armed')
else:
    print('Could not arm...')
"""

"""
marker_dict   = aruco.Dictionary_get(aruco.DICT_6X6_1000)
param_markers = aruco.DetectorParameters_create()
"""

#arm_and_takeoff(3)

print("Starting mission")

"""

if vehicle.mode != 'STABILIZE':
    vehicle.wait_for_mode('STABILIZE')
    print('Mode: ', vehicle.mode)
"""

#if vehicle.mode != 'AUTO':
#    vehicle.wait_for_mode('AUTO')
#    print('Mode: ', vehicle.mode)

                """
                Expect drone to identify the marker, then loiter in place for 10 seconds, before continuing on
                  through the rest of it's flight
                """
                #time.sleep(10)
                
                # Turn the laser on
                msg = vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_SET_SERVO,0,
                    6,    # Channel
                    1900, # PWM, between 1100 - 1900
                    0,0,0,0,0       
                )

                vehicle.send_mavlink(msg)
                output = "  Laser turned  on for ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")
                
                # This time.sleep influences how long the laser is on
                time.sleep(0.5)

                # Turn the laser off
                msg = vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_SET_SERVO,0,
                    6,    # Channel
                    0,    # PWM, between 1100 - 1900
                    0,0,0,0,0       
                )

                vehicle.send_mavlink(msg)
