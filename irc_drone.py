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
                and a specified channel. Both UAVBot and UGVHitListener inherrit from
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
        print("{} connected to {} and joined {}".format(self.__class__.__name__, self.server, self.channel))

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
    def send_fire_message(self, team_name, aruco_id, time, location):
        # Format the message with the given information
        # TODO: Verify that this message format is correct
        message = "RTXDC_2023 {}_UAV_Fire_{}_{}_{}".format(
            team_name, aruco_id, time.strftime("%m-%d-%Y %H:%M:%S"), location)

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

        self.aruco_id  = None
        self.markerID  = None

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
            #self.aruco_id = parts[1]
            aruco_id      = parts[1]
            time_stamp    = parts[2]
            gps_location  = parts[3]

            current_time     = datetime.now()
            date_time_object = datetime.strptime(time_stamp, "%m-%d-%Y %H:%M:%S") # This format matters, maybe look at getting the time from the IRC server message

            # Check if the message was received in the last set amount of time in seconds
            if current_time - date_time_object <= timedelta(seconds = 20):
                # Add the arucoID to self.aruco_id if all these requirements are met
                self.aruco_id = aruco_id
                print(f"Received hit confirmation for markerID {self.markerID} at time {time_stamp} and location {gps_location}")

# Create a function to run the IRC bot in a separate thread
def run_bot(bot):
    bot.start()

"""
Attempt to stop the Pi Camera debug error from coming up
    If the debug errors still show up, remove everything from this block and
    only keep logging.basicConfig(filename = 'debug.log', level = logging.INFO)
"""
console_handler = logging.StreamHandler()       # Create a logging handler that logs warnings and above to the console
console_handler.setLevel(logging.WARNING)
logging.getLogger().addHandler(console_handler) # Add the console logging handler to the root logger
logging.getLogger().setLevel(logging.WARNING)   # Set the root logger's level to warnings and above

# Initializing PiCamera2 object with main preview configuration set to XRGB8888 format and 640x480 resolution
picam2 = Picamera2(verbose_console=0)
picam2.configure(picam2.create_preview_configuration(main = {"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# Start a video recording and saving it to a file with a name based on the current time stamp
#picam2.start_and_record_video("flight recording " + str(time.strftime("%m-%d-%y  %I:%M:%S %p", time.localtime())) + ".mp4")

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

# Set the connection string to the USB port that the drone is connected to
connection_string = '/dev/ttyUSB0'

print('Connecting to vehicle on: ', connection_string)

# Connect to the drone with the specified connection string and baud rate
#   Wait until the drone is ready before continuing
vehicle = connect(connection_string,baud = 57600, wait_ready = True)

# Print a message indicating that the program has successfully connected to the drone
print('Connected')

"""
# Arm the drone
print('Arming...')
vehicle.arm()
"""

# Check if the drone has been armed. If it has, print a message indicating that the drone has been armed
#   If it has not, print a message indicating that the drone could not be armed
"""
if vehicle.armed == True:
    print('Armed')
else:
    print('Could not arm...')
"""
    
file = open("log_marker_flight.txt","w")              # Create a new text file to log data to
file.write("============= BEGIN LOG =============\n") # Write a line to the file to indicate the start of the log

marker_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000) # Load the 6x6 ArUco marker dictionary with 1000 markers
param_markers = cv2.aruco.DetectorParameters()                             # Set the parameters for the marker detector
detector      = cv2.aruco.ArucoDetector(marker_dict, param_markers)        # Create an instance of the ArUco detector using the marker dictionary and parameters

# A list for the IDs we find
markerID_list = []

#arm_and_takeoff(3)
"""
print("Starting mission")
if vehicle.mode != 'STABILIZE':
    vehicle.wait_for_mode('STABILIZE')
    print('Mode: ', vehicle.mode)
"""
"""
if vehicle.mode != 'AUTO':
    vehicle.wait_for_mode('AUTO')
    print('Mode: ', vehicle.mode)
"""

print("\nNow looking for ArUco Markers...\n")

cur_time = datetime.now()
print(str(cur_time))

# While the vehicle is armed, look for and shoot at markers
#while vehicle.armed == True:
while True:
    frame      = picam2.capture_array()
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # corners  - A list of detected marker corners, where each element is an array of four corner points in pixel coordinates
    # ids      - A list of detected marker IDs, where each element corresponds to the marker at the corresponding index in the corners list
    # rejected - A list of rejected candidate marker corners that did not meet the detection criteria
    (corners, ids, rejected) = aruco.detectMarkers(
        gray_frame,                 # The input grayscale image in which the markers will be detected
        marker_dict,                # The dictionary of markers used for detection
        parameters = param_markers  # Optional parameters for detection
    )
    
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
            
            # Add marker ID to a list, check if ID in list, if in list do not log again
            if markerID not in markerID_list:
                
                #print("ID list: " + str(markerID_list))
                output = "Found ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")
                
                # Loiter drone if ID found
                ###vehicle.mode = VehicleMode("LOITER")
                #vehicle.wait_for_mode('LOITER')

                """
                Expect drone to identify the marker, then loiter in place for 10 seconds, before continuing on
                  through the rest of it's flight
                """
                #time.sleep(10)
                
                # Turn the laser on
                msg = vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_SET_SERVO, 0,
                    6,    # Channel
                    1900, # PWM, between 1100 - 1900
                    0,0,0,0,0       
                )

                vehicle.send_mavlink(msg)
                output = "  Laser turned  on for ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p", time.localtime()))
                print(output)
                file.write(output + "\n")
                
                # This time.sleep influences how long the laser is on
                time.sleep(0.25)

                # Turn the laser off
                msg = vehicle.message_factory.command_long_encode(
                    0,0,
                    mavutil.mavlink.MAV_CMD_DO_SET_SERVO, 0,
                    6,    # Channel
                    0,    # PWM, between 1100 - 1900
                    0,0,0,0,0       
                )

                vehicle.send_mavlink(msg)

                output = "  Laser turned off for ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p", time.localtime()))
                print(output)
                file.write(output + "\n")

                """
                ------------------------------------------------------------------------------------
                                                IRC Bot Interaction
                ------------------------------------------------------------------------------------
                """
                # Try to give the listener the current marker ID it is looking at -----------------------------------------------------------
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
                
                time.sleep(1)

                print("Bot ID: " + str(listener.aruco_id))

                # Check to see if the aruco ID from IRC is the same as the current marker
                #   If it is, add it to the list so we do not shoot at it again
                if listener.aruco_id != None and int(markerID) not in markerID_list:
                    print("Here inside the bot check loop.")
                    if int(listener.aruco_id) == int(markerID):
                        print("Found {}".format(listener.aruco_id))
                        markerID_list.append(markerID)
                        print("Added {} to list".format(listener.aruco_id))

                ####vehicle.mode = VehicleMode("AUTO")
                
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
