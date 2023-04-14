from   dronekit           import connect, VehicleMode, LocationGlobalRelative, APIException
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

###################################################################################
# This file requires the mission to have a return to launch/landing waypoint
###################################################################################

"""
    @brief: IRCBot inherits from the irc.client.SimpleIRCClient class. It represents a
                basic template for creating an IRC bot, which connects to an IRC server
                and a specified channel. Both UAVBot and UGVHitListener inherit from
                this class
"""
class IRCBot(irc.client.SimpleIRCClient):
    def __init__(self, bot_name, server, channel):
        # Initialize the bot by connecting to the IRC server and joining the channel
        irc.client.SimpleIRCClient.__init__(self)

        # Set the server and channel information
        self.server  = server
        self.channel = channel

        # Set the bot's initial connection status to False
        self.connected = False

        # Connect the bot to the server and join the channel
        self.connect(self.server, 6667, bot_name)
        self.connection.join(self.channel)

    def on_welcome(self, connection, event):
        # When the bot successfully joins the channel, set its connection status to True
        connection.join(self.channel)
        self.connected = True
        print(f"{self.__class__.__name__} connected to {self.server} and joined {self.channel}")
    
    # Disconnect the bot from the server
    def end(self, bot_name):
        # Check if the bot is currently connected to the server
        if self.connected:
            self.connection.part(self.channel)                                    # Leave the channel the bot is currently in
            self.connection.quit(bot_name + " is disconnecting from the server.") # Send a quit message to the IRC server and disconnect the bot
            self.connected = False

"""
    @brief: UAVBot is an IRC bot that joins the IRC server and sends messages
                when the drone fires its laser. The message contains all the
                content required by Raytheon
"""
class UAVBot(IRCBot):
    def __init__(self):
        # Call the parent constructor to connect to the IRC server and join the channel
        IRCBot.__init__(self, "UTA_UAVBot", "irc.libera.chat", "#RTXDrone")

    # Send fire message to channel
    def send_fire_message(self, team_name, aruco_id, time_of_laser, location):
        # Raytheon says only send a message per second?
        time.sleep(1)
        # Format the message with the given information
        # TODO: Verify that this message format is correct
        #       Timestamp needs to be in central time!!!!!
        time_of_fire = time_of_laser.strftime("%m-%d-%Y %I:%M:%S")
        message      = f"RTXDC_2023 {team_name}_UAV_Fire_{aruco_id}_{time_of_fire}_{location}"

        # Send the message to the channel
        self.connection.privmsg(self.channel, message)


"""
    @brief: UGVHitListener is an IRC bot that joins the IRC server and listens
                for messages in the server chat that contain _UGV_Hit_. If it
                finds a message, it then takes it and gets the ArUco ID of the
                vehicle that said it was hit
"""
class UGVHitListener(IRCBot):
    def __init__(self):
        # Call the parent constructor to connect to the IRC server and join the channel
        IRCBot.__init__(self, "UGV_HitListener", "irc.libera.chat", "#RTXDrone")

        self.aruco_id  = None # The aruco_id from the server
        self.markerID  = None # The marker ID the drone is currently looking at

    # This will constantly listen for public messages sent in the channel
    def on_pubmsg(self, connection, event):
        # Message format: RTXDC_2023 UTA_UGV_Hit_134_04-03-2023 11:38:57_0.0_0.0

        # Parse incoming message and extract hit information
        message = event.arguments[0]

        # Only look at messages in the server that contain the ID of the vehicle we are currently looking at
        if f"_UGV_Hit_{self.markerID}" in message:
            # Remove the UGV_Hit part of the received message so it is easier to split
            new_message = message.replace("RTXDC_2023 ", "").replace("UGV_Hit_", "")

            # Split the message into parts and extract the required information
            parts         = new_message.split("_")
            self.aruco_id = parts[1]
                
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

# Create a logger to ignore the Pi Camera debug error
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
logging.getLogger().addHandler(console_handler)
logging.getLogger().setLevel(logging.WARNING)

#cv2.startWindowThread()
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main = {"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
#picam2.start_and_record_video("flight recording " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime())) + ".mp4")

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

print("Made it past the IRC bot initialization")

############################################################
############################################################
############################################################

connection_string = '/dev/ttyUSB0'

print('Connecting to vehicle on: ', connection_string)
vehicle = connect(connection_string,baud = 57600, wait_ready = True)
print('Connected')

# Make the mode stabilize so that we don't get "auto mode not armable"
#   This will be switched to auto after the drone is armed
if vehicle.mode != 'STABILIZE':
    vehicle.wait_for_mode('STABILIZE')
    print('Mode: ', vehicle.mode)

print('Arming...')
vehicle.arm()

if vehicle.armed == True:
    print('Armed')
else:
    print('Could not arm...')

#arm_and_takeoff(6)
"""
if vehicle.mode != 'STABILIZE':
    vehicle.wait_for_mode('STABILIZE')
    print('Mode: ', vehicle.mode)
"""

if vehicle.mode != 'AUTO':
    vehicle.wait_for_mode('AUTO')
    print('Mode: ', vehicle.mode)

print("Starting mission")
    
filename = "log.txt"

with open(filename, "w") as file:
    file.write("============= BEGIN LOG =============\n")

marker_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000)
param_markers = cv2.aruco.DetectorParameters()
detector      = cv2.aruco.ArucoDetector(marker_dict, param_markers)

# A list for the IDs we find
markerID_list     = [42]    # UTA Official ID: 42
friendly_detected = False

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
                print(f"Friendly detected: ID: {markerID}")
                print("   Not firing laser")
            
            # Check if ID in list, add marker ID to a list if it is not in the list,  if in list do not log again
            if markerID not in markerID_list:
                
                #print("ID list: " + str(markerID_list))
                #output = "Found ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                output = f"Found ID: {markerID}    TIME: {time.strftime('%m-%d-%y  %I:%M:%S %p', time.localtime())}"
                print(output)
                with open(filename, "a") as file:
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
                #output = "  Laser turned  on for ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p", time.localtime()))
                output = f"  Laser turned on for ID: {markerID}    TIME: {time.strftime('%m-%d-%y  %I:%M:%S %p', time.localtime())}"
                print(output)
                with open(filename, "a") as file:
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

                #output = "  Laser turned off for ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                output = f"  Laser turned off for ID: {markerID}    TIME: {time.strftime('%m-%d-%y  %I:%M:%S %p', time.localtime())}"
                print(output)
                with open(filename, "a") as file:
                    file.write(output + "\n")

                """
                ------------------------------------------------------------------------------------
                                                IRC Bot Interaction
                ------------------------------------------------------------------------------------
                """
                # Try to give the listener the current marker ID it is looking at
                listener.markerID = markerID
                print(f"listener.markerID is looking for IRC messages with ID: {listener.markerID}")

                # Pull GPS Coordinates latitude and longitude from Mavlink stream
                lat  = vehicle.location.global_relative_frame.lat
                lon  = vehicle.location.global_relative_frame.lon

                # Write GPS part of string message, convert GPS coords to strings so it can be encoded 
                location     = f"{lat}_{lon}"
                team_name    = "UTA"
                current_time = datetime.now()

                # Send fire message to server
                uav_bot.send_fire_message(team_name, str(markerID), current_time, location)

                print(f"Marker ID currently in UGV_HitListener:  {listener.aruco_id}")

                # Check to see if the aruco ID from IRC is the same as the current marker
                #   If it is, add it to the list so we do not shoot at it again
                if listener.aruco_id != None and int(markerID) not in markerID_list:
                    print("Checking for hit verification...")
                    if int(listener.aruco_id) == int(markerID):
                        print(f"Found {listener.aruco_id}")
                        markerID_list.append(markerID)
                        print(f"Added {listener.aruco_id} to list")

vehicle.close()
output = "\nBots now leaving the IRC server...\n============== END LOG ==============\n\n"
with open(filename, "a") as file:
    file.write(output + "\n")

# End the IRC bot connections and wait for the threads to finish
uav_bot.end("UTA_UAVBot")
listener.end("UGV_HitListener")

time.sleep(1)

#picam2.stop_recording()
exit()
