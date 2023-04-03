import irc.client
import irc.bot
import threading

"""
    @brief: UAVBot is an IRC bot that joins the IRC server and sends messages
                when the drone fires its laser. The message contains all the
                content required by Raytheon
"""
class UAVBot(irc.client.SimpleIRCClient):
    def __init__(self):
        # Initialize the bot by connecting to the IRC server and joining the channel
        irc.client.SimpleIRCClient.__init__(self)

        # Set the server and channel information
        self.server  = "irc.libera.chat"
        self.channel = "#RTXDrone"

        # Set the bot's initial connection status to False
        self.connected = False

        # Connect the bot to the server and join the channel
        self.connect(self.server, 6667, "UTA_UAVBot")
        self.connection.join(self.channel)

    def on_welcome(self, connection, event):
        # When the bot successfully joins the channel, set its connection status to True
        connection.join(self.channel)
        self.connected = True
        print("UAVBot connected to {} and joined {}".format(self.server, self.channel))

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
class UGVHitListener(irc.client.SimpleIRCClient):
    def __init__(self):
        # Initialize the bot by connecting to the IRC server and joining the channel
        irc.client.SimpleIRCClient.__init__(self)

        # Set the server and channel information
        self.server  = "irc.libera.chat"
        self.channel = "#RTXDrone"

        # Set the bot's initial connection status to False and the current aruco_id to None
        self.connected = False
        self.aruco_id  = None

        # Connect the bot to the server and join the channel
        self.connect(self.server, 6667, "UGV_HitListener")
        self.connection.join(self.channel)

    def on_welcome(self, connection, event):
        # When the bot successfully joins the channel, set its connection status to True
        connection.join(self.channel)
        self.connected = True
        print("UGVHitListener connected to {} and joined {}".format(self.server, self.channel))

    # This will constantly listen for public messages sent in the channel
    def on_pubmsg(self, connection, event):
        # Parse incoming message and extract hit information
        message = event.arguments[0]

        # TODO: Maybe look at a way to make this search for only the string containing the
        #       ID we are currently shooting at
        if "_UGV_Hit_" in message:
            # Remove the UGV_Hit part of the received message so it is easier to split
            new_message = message.replace("RTXDC_2023 ", "").replace("UGV_Hit_", "")

            # Split the message into parts and extract the required information
            parts         = new_message.split("_")
            self.aruco_id = parts[1]
            time_stamp    = parts[2]
            gps_location  = parts[3]
            print("Received hit confirmation for aruco_id {} at time {} and location {}".format(self.aruco_id, time_stamp, gps_location))
            # TODO: If this runs continuously, is there any way to check the messages after we fire?

# Create a function to run the IRC bot in a separate thread
def run_bot(bot):
    bot.start()
