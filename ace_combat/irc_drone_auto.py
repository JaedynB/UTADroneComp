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

"""
if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    from collection.abc import MutableMapping
else:
    from collections import MutableMapping
"""

###################################################################################
# This file requires the mission to have a return to launch/landing waypoint
###################################################################################

class UAVBot(irc.client.SimpleIRCClient):
    def __init__(self):
        # Connect to IRC server and join channel
        #   Get the info from here: https://github.com/cmm6758/IRCScript/blob/main/irchan.py
        irc.client.SimpleIRCClient.__init__(self)
        self.server    = "irc.libera.chat"
        self.channel   = "#RTXDrone"
        self.connected = False
        self.connect(self.server, 6667, "UTA_UAV_CSE")
        self.connection.join(self.channel)

    def on_welcome(self, connection, event):
        connection.join(self.channel)
        self.connected = True  # Set connected to True when the bot joins the channel
        print("UAVBot connected to {} and joined {}".format(self.server, self.channel))

    # Send fire message to channel
    def send_fire_message(self, team_name, aruco_id, time, location):
        # TODO: Make sure this message format is correct
        message = "RTXDC_2023 {}_UAV_Fire_{}_{}_{}".format(
            team_name, aruco_id, time.strftime("%m-%d-%Y %I:%M:%S %p"), location)
        self.connection.privmsg(self.channel, message)

class UGVHitListener(irc.client.SimpleIRCClient):
    def __init__(self):
        irc.client.SimpleIRCClient.__init__(self)
        self.server    = "irc.libera.chat"
        self.channel   = "#RTXDrone"
        self.connected = False
        self.aruco_id  = None
        self.connect(self.server, 6667, "UGV_HitListener")
        self.connection.join(self.channel)

    def on_welcome(self, connection, event):
        connection.join(self.channel)
        self.connected = True  # Set connected to True when the bot joins the channel
        print("UGVHitListener connected to {} and joined {}".format(self.server, self.channel))

    # This will constantly listen for public messages sent in the channel
    def on_pubmsg(self, connection, event):
        # Parse incoming message and extract hit information
        message = event.arguments[0]

        # TODO: Maybe look at a way to make this search for only the string containing the
        #       ID we are currently shooting at
        if "_UGV_Hit_" in message:
            # Remove the UGV_Hit part of the recieved message so it is easier to split
            #   In the SOW the UGV_Hit__ has two __, did they mean UGV_Hit_ with one _?
            # RTXDC_2023 UTA_UGV_Hit_5_12:00_[GPS location]
            # UTA_5_12:00_[GPS location]
            new_message = message.replace("RTXDC_2023 ", "").replace("UGV_Hit_", "")
            print("New message: " + new_message)

            parts         = new_message.split("_")
            self.aruco_id = parts[1]
            time_stamp    = parts[2]
            gps_location  = parts[3]
            print("Received hit confirmation for aruco_id {} at time {} and location {}".format(self.aruco_id, time_stamp, gps_location))
            # TODO: If this runs continuously, is there any way to check the messages after we fire?

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

"""
Attempt to stop the Pi Camera debug error from coming up
    If the debug errors still show up, remove everything from this block and
    only keep logging.basicConfig(filename = 'debug.log', level = logging.INFO)
"""
#logging.basicConfig(filename = 'debug.log', level = logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
logging.getLogger().addHandler(console_handler)
logging.getLogger().setLevel(logging.WARNING)

############################################################
####################### IRC BOTS ###########################
############################################################

# Create a function to run the IRC bot in a separate thread
def run_bot(bot):
    bot.start()

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

# The program can continue running here while the bots are connected to the IRC channel

print("Made it past the IRC bot initialization")

############################################################
############################################################
############################################################

#cv2.startWindowThread()
picam2 = Picamera2(verbose_console=0)
picam2.configure(picam2.create_preview_configuration(main = {"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
#picam2.start_and_record_video("flight recording " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime())) + ".mp4")

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

file = open("log_marker_flight.txt","w")
file.write("============= BEGIN LOG =============\n")

# Aruco Marker
# Changed the ArUco dictionary to 6x6 because that is what is specified by Raytheon
#marker_dict   = aruco.Dictionary_get(aruco.DICT_6X6_250)
# Proposed fix for marker detection during flight to change the marker dictionary.
marker_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000)
param_markers = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(marker_dict, param_markers)
"""
marker_dict   = aruco.Dictionary_get(aruco.DICT_6X6_1000)
param_markers = aruco.DetectorParameters_create()
"""

# A list for the IDs we find
markerID_list     = [42]
friendly_detected = False

arm_and_takeoff(3)

print("Starting mission")

"""
if vehicle.mode != 'STABILIZE':
    vehicle.wait_for_mode('STABILIZE')
    print('Mode: ', vehicle.mode)
"""

if vehicle.mode != 'AUTO':
    vehicle.wait_for_mode('AUTO')
    print('Mode: ', vehicle.mode)

print("\nNow looking for ArUco Markers...\n")

# Aruco
while True:
    frame      = picam2.capture_array()
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    (corners, ids, rejected) = aruco.detectMarkers(
        gray_frame,
        marker_dict,
        parameters = param_markers
    )
    
    if len(corners) > 0:
        
        ids = ids.flatten()
        
        for (markerCorner, markerID) in zip(corners, ids):
            corners = markerCorner.reshape((4, 2))
            
            (topLeft, topRight, bottomRight, bottomLeft) = corners
            
            topRight    = (int(topRight[0]),    int(topRight[1]))
            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
            bottomLeft  = (int(bottomLeft[0]),  int(bottomLeft[1]))
            topLeft     = (int(topLeft[0]),     int(topLeft[1]))
            
            """
            # Draw
            cv2.line(frame, topLeft, topRight, (0, 255, 0), 2)
            cv2.line(frame, topRight, bottomRight, (0, 255, 0), 2)
            cv2.line(frame, bottomRight, bottomLeft, (0, 255, 0), 2)
            cv2.line(frame, bottomLeft, topLeft, (0, 255, 0), 2)
            """
            
            """
            # Computing and drawing the center of the ArUco marker
            #cX = int((topLeft[0] + bottomRight[0]) / 2.0)
            #cY = int((topLeft[1] + bottomRight[1]) / 2.0)
            """
            #cv2.circle(frame, (cX, cY), 4, (0, 0, 255) -1)
            
            """
            cv2.polylines(frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv2.LINE_AA)
            cv2.putText(frame, str(markerID), (topLeft[0], topLeft[1] - 15), cv2.FONT_HERSHEY_PLAIN, 1.6 , (200, 100, 0), 2, cv2.LINE_AA)
            """
            
            if int(markerID) == 14 and friendly_detected == False:
                friendly_detected = True
                print("Friendly detected: ID: " + str(markerID))
            
            # Add marker ID to a list, check if ID in list, if in list do not log again
            if markerID not in markerID_list and (int(markerID) != 14):
                
                #print("ID list: " + str(markerID_list))
                output = "Found ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")
                
                # Loiter drone if ID found
                vehicle.mode = VehicleMode("LOITER")
                vehicle.wait_for_mode('LOITER')

                """
                Expect drone to identify the marker, then loiter in place for 10 seconds, before continuing on
                  through the rest of it's flight
                """
                time.sleep(5)
                
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

                output = "  Laser turned off for ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")

                ##################################################################
                ##################################################################
                ##################################################################

                # Pull GPS Coordinates latitude and longitude from Mavlink stream
                lat  = vehicle.location.global_relative_frame.lat
                lon  = vehicle.location.global_relative_frame.lon

                # Convert GPS coords from int to strings so it can be encoded 
                lat_str = str(lat)
                lon_str = str(lon)

                # Write GPS part of string Message
                location     = 'lat_' + lat_str + '_long_' + lon_str
                #location = "Lab"
                team_name    = "UTA"
                current_time = datetime.datetime.now()

                # Send fire message to server
                uav_bot.send_fire_message(team_name, str(markerID), current_time, location)
                
                time.sleep(1)
                
                print("Bot ID: " + str(listener.aruco_id))
                
                # Check to see if the aruco ID from IRC is the same as the current marker
                #   If it is, add it to the list so we do not shoot at it again
                #if listener.aruco_id != None and str(markerID) not in markerID_list:
                if listener.aruco_id != None and int(markerID) not in markerID_list:
                    print("Here inside the bot check loop.")
                    if int(listener.aruco_id) == int(markerID):
                        print("Found {}".format(listener.aruco_id))
                        markerID_list.append(markerID)
                        print("Added {} to list".format(listener.aruco_id))

                vehicle.mode = VehicleMode("AUTO")
                
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
