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


#"""
print('Arming...')
vehicle.arm()


if vehicle.armed == True:
    print('Armed')
else:
    print('Could not arm...')
#"""

# Set vehicle mode to GUIDED and arm the drone
vehicle.mode = VehicleMode("GUIDED")
vehicle.armed = True

# Wait for the vehicle to arm and enter GUIDED mode
while not vehicle.mode.name=='GUIDED' and not vehicle.armed:
    print("Waiting for drone to arm and enter GUIDED mode...")
    time.sleep(1)

# Define a function to send MAVLink commands to the vehicle
def send_command( command ):
    vehicle.send_mavlink(command)
    vehicle.flush()

# Define a function to takeoff the drone to a certain altitude
def takeoff( altitude ):
    # Take off to the specified altitude
    send_command(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, altitude)

    # Wait for the drone to reach the desired altitude
    while vehicle.location.global_relative_frame.alt < altitude:
        print("Drone is taking off...")
        time.sleep(1)

    print("Drone reached desired altitude")

# Define a function to land the drone
def land():
    # Land the drone
    send_command(mavutil.mavlink.MAV_CMD_NAV_LAND, 0, 0, 0, 0, 0, 0, 0)

    # Wait for the drone to land
    while vehicle.location.global_relative_frame.alt > 0:
        print("Drone is landing...")
        time.sleep(1)

    print("Drone landed safely")

# Takeoff to a height of 2 meters
takeoff(2)

# Fly forward for 5 seconds
send_command(mavutil.mavlink.MAV_CMD_NAV_GUIDED_ENABLE, 0, 0, 0, 0, 0, 0, 1)
send_command(mavutil.mavlink.MAV_CMD_CONDITION_YAW, 0, 0, 0, 0, 30, 0, 1)
send_command(mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0)

# Land the drone
land()

# Disarm the drone
vehicle.armed = False

# Close the vehicle object
vehicle.close()
