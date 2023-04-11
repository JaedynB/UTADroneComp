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

def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

    print("Basic pre-arm checks")
    
    # Don't let the user try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    
    # Copter should arm in GUIDED mode
    vehicle.mode  = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95: #Trigger just below target alt.
            print("Reached target altitude")
            break
        time.sleep(1)

# Capture the current frame from the Pi Camera
def capture_frame():
    frame      = picam2.capture_array()
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    return frame, gray_frame

# Try to detect any ArUco markers in the current frame
def detect_markers(gray_frame):
    # corners  - A list of detected marker corners, where each element is an array of four corner points in pixel coordinates
    # ids      - A list of detected marker IDs, where each element corresponds to the marker at the corresponding index in the corners list
    # rejected - A list of rejected candidate marker corners that did not meet the detection criteria
    (corners, ids, rejected) = aruco.detectMarkers(
        gray_frame,                 # The input grayscale image in which the markers will be detected
        marker_dict,                # The dictionary of markers used for detection
        parameters = param_markers  # Optional parameters for detection
    )

    return corners, ids, rejected

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

"""
Attempt to stop the Pi Camera debug error from coming up
    If the debug errors still show up, remove everything from this block and
    only keep logging.basicConfig(filename = 'debug.log', level = logging.INFO)
"""
console_handler = logging.StreamHandler()       # Create a logging handler that logs warnings and above to the console
console_handler.setLevel(logging.WARNING)
logging.getLogger().addHandler(console_handler) # Add the console logging handler to the root logger
logging.getLogger().setLevel(logging.WARNING)   # Set the root logger's level to warnings and above

# Set the connection string to the USB port that the drone is connected to
connection_string = '/dev/ttyUSB0'

print('Connecting to vehicle on: ', connection_string)

# Connect to the drone with the specified connection string and baud rate
#   Wait until the drone is ready before continuing
vehicle = connect(connection_string,baud = 57600, wait_ready = True)

# Print a message indicating that the program has successfully connected to the drone
print('Connected')

# Arm the drone
print('Arming...')
vehicle.arm()

# Check if the drone has been armed. If it has, print a message indicating that the drone has been armed
#   If it has not, print a message indicating that the drone could not be armed
if vehicle.armed == True:
    print('Armed')
else:
    print('Could not arm...')

file = open("log_marker_flight.txt","w")              # Create a new text file to log data to
file.write("============= BEGIN LOG =============\n") # Write a line to the file to indicate the start of the log

#arm_and_takeoff(3)

print("Starting mission")

if vehicle.mode != 'STABILIZE':
    vehicle.wait_for_mode('STABILIZE')
    print('Mode: ', vehicle.mode)

"""
if vehicle.mode != 'AUTO':
    vehicle.wait_for_mode('AUTO')
    print('Mode: ', vehicle.mode)
"""

print("\nNow looking for ArUco Markers...\n")

# ArUco detection while the drone is armed
while vehicle.armed == True:
    frame, gray_frame      = capture_frame()
    corners, ids, rejected = detect_markers(gray_frame)
    
    # If any markers are detected in the image
    if len(corners) > 0:
        
        # Flatten the IDs array to make it easier to work with
        ids = ids.flatten()
        
        # Loop over all detected markers and their corners
        for (markerCorner, markerID) in zip(corners, ids):
            corners = markerCorner.reshape((4, 2))
            
            # Extract the four corner points of the detected marker
            (topLeft, topRight, bottomRight, bottomLeft) = corners
            
            # Convert the corner points to integer coordinates
            topRight    = (int(topRight[0]),    int(topRight[1]))
            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
            bottomLeft  = (int(bottomLeft[0]),  int(bottomLeft[1]))
            topLeft     = (int(topLeft[0]),     int(topLeft[1]))
            
            # Check to see if we found the friendly marker
            if int(markerID) == 42 and friendly_detected == False:
                friendly_detected = True
                print("Friendly detected: ID: " + str(markerID))
                print("   Not firing laser")
            
            # Check if ID in list, add marker ID to a list if it is not in the list,  if in list do not log again
            if markerID not in markerID_list:
                
                #print("ID list: " + str(markerID_list))
                output = "Found ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")
                
                 # Turn the laser on
                msg = vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_SET_SERVO,0,
                    6,    # Channel
                    1900, # PWM, between 1100 - 1900
                    0,0,0,0,0       
                )

                vehicle.send_mavlink(msg)
                output = "  Laser turned  on for ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p", time.localtime()))
                print(output)
                file.write(output + "\n")
                
                # LED strip on
                msg = vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_SET_RELAY,0,
                    0, # Channel
                    1, # PWM, between 1100 - 1900
                    0,0,0,0,0       
                )

                vehicle.send_mavlink(msg)

                # This time.sleep influences how long the laser is on
                time.sleep(0.1) # Was 0.25, maybe go lower?

                # Turn the laser off
                msg = vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_SET_SERVO,0,
                    6,    # Channel
                    0,    # PWM, between 1100 - 1900
                    0,0,0,0,0       
                )

                vehicle.send_mavlink(msg)

                # LED OFF
                msg = vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_SET_RELAY,0,
                    0, # Channel
                    0, # PWM, between 1100 - 1900
                    0,0,0,0,0       
                )

                vehicle.send_mavlink(msg)
                
                time.sleep(0.1) # Was 0.5

                # Sound buzzer when firing. Plays a single C note
                vehicle.play_tune(bytes('C','utf-8'))

                output = "  Laser turned off for ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")

                """
                ------------------------------------------------------------------------------------
                                                IRC Bot Interaction
                ------------------------------------------------------------------------------------
                """
                # Try to give the listener the current marker ID it is looking at
                listener.markerID = markerID
                print("listener.markerID = " + str(listener.markerID))

                # Pull GPS Coordinates latitude and longitude from Mavlink stream
                lat  = vehicle.location.global_relative_frame.lat
                lon  = vehicle.location.global_relative_frame.lon

                # Write GPS part of string message, convert GPS coords to strings so it can be encoded 
                location     = str(lat) + '_' + str(lon)
                team_name    = "UTA"
                current_time = datetime.now()

                # Send fire message to server
                uav_bot.send_fire_message(team_name, str(markerID), current_time, location)

                print("Bot ID: " + str(listener.aruco_id))

                # Check to see if the aruco ID from IRC is the same as the current marker
                #   If it is, add it to the list so we do not shoot at it again
                if listener.aruco_id != None and int(markerID) not in markerID_list:
                    print("Here inside the bot check loop.")
                    if int(listener.aruco_id) == int(markerID):
                        print("Found {}".format(listener.aruco_id))
                        markerID_list.append(markerID)
                        print("Added {} to list".format(listener.aruco_id))


# End the IRC bot connections and wait for the threads to finish
uav_bot.end()
listener.end()

uav_thread.join()
listener_thread.join()

file.write("============== END LOG ==============\n\n")
file.close()

vehicle.close()
#picam2.stop_recording()
exit()
