import irc.client
import irc.bot
import threading
import time
from   datetime           import datetime, timedelta

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
        self.aruco_id = None  # The aruco_id from the server
        self.markerID = None  # The marker ID the drone is currently looking at

    # This will constantly listen for public messages sent in the channel
    def on_pubmsg(self, connection, event):
        # Message format: RTXDC_2023 UTA_UGV_Hit_134_04-03-2023 11:38:57_0.0_0.0

        # Parse incoming message and extract hit information
        message = event.arguments[0]
        print("Here: " + str(event.tags))

        # Only look at messages in the server that contain the ID of the vehicle we are currently looking at
        if f"_UGV_Hit_" in message:
            # Remove the UGV_Hit part of the received message so it is easier to split
            new_message   = message.replace("RTXDC_2023 ", "").replace("UGV_Hit_", "")
            parts         = new_message.split("_")
            aruco_id      = parts[1]

            print(str(event.tags))

            # Extract the timestamp from event.source
            time_stamp = event.source.split()[1]
            # Parse the timestamp from event.source to get the official server time
            date_time_object = datetime.strptime(time_stamp, "%H:%M:%S")
            print("Time from IRC server: " + str(date_time_object))

            current_time = datetime.now()

            # Check if the message was received in the last set amount of time in seconds
            if current_time - date_time_object <= timedelta(seconds=3):
                # Add the arucoID to self.aruco_id if all these requirements are met
                self.aruco_id = aruco_id
                print(f"Received hit confirmation for markerID {self.markerID} at time {time_stamp} and location {gps_location}")


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

# Listen for message until the program is ended
while True:
    time.sleep(2)
    #print(listener.aruco_id)
    if listener.aruco_id != None:
        print("Found {}".format(listener.aruco_id))
