import time
import irc.client
import irc.bot
import datetime
import threading

"""
    Two classes are created in this Python program, UAVBot and UGVHitListener. These are two IRC bots that send and listen to IRC channels. The bots
        should be run in separate threads since if they weren't, the program wouldn't be able to move past the initialization of the IRC bots. As long
        as the program is running, both bots will listen and send information. This eliminates the need for constant pings to the server.
        UAVBot is used to send the hit information required in the statement of work.
        When a message is posted on the IRC channel and the bot has connected, UGVHitListener listens for that message and gets the ArUco ID from it.
    This program was written by Robert. If you have questions, feel free to ask.
"""

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
            new_message = message.replace("RTXDC_2023 ", "").replace("UGV_Hit_", "")
            print(new_message)

            parts         = new_message.split("_")
            self.aruco_id = parts[1]
            time_stamp    = parts[2]
            gps_location  = parts[3]
            print("Received hit confirmation for aruco_id {} at time {} and location {}".format(self.aruco_id, time_stamp, gps_location))
            # TODO: If this runs continuously, is there any way to check the messages after we fire?

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

print("Made it past the initialization")

# Send the fire message to the server
team_name    = "UTA_UAV_CSE"
aruco_id     = "1"
current_time = datetime.datetime.now()
location     = "40.7128° N, 74.0060° W"
uav_bot.send_fire_message(team_name, aruco_id, current_time, location)

print("Message has been sent")

"""
Required message formats for UGV_Hit messages:
    RTXDC_2023 [SchoolName]_UGV_Hit__[UGV_ArucoMarkerID]_[timestamp]_[GPS location]
    RTXDC_2023 UTA_UGV_Hit_5_12:00_[GPS location]
"""

# List of IDs with confirmed hits
id_list = []

list_check = [1, 15, 23, 50, 65]

# Listen for message until the program is ended
while True:
    time.sleep(1)
    #print(listener.aruco_id)
    if listener.aruco_id != None and list_check not in id_list:
        #print("Here!")
        if int(listener.aruco_id) in list_check:
            print("Found {}".format(listener.aruco_id))
            id_list.append(listener.aruco_id)
