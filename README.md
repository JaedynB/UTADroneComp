*README.md still under construction*
# UTA Raytheon Drone Competition 2022

## Table of Contents
- UTA Raytheon Drone Competition
  * [About the Project](#about-the-project)
  * [Compile Instructions](#compile-instructions)
  * [Detailed Code Description](#detailed-code-description)

## About the Project
This is a repository containing the Raytheon Drone Competition's software. Currently, Robert Carr, Ja'lun Morris, Jaedyn Brown, Pearl Iyayi, and Javier Lopez make up the software development team.

Software development team lead Javier Lopez serves as the point of contact.

## Compile Instructions
***We are using Python version 3.9***
1. Download project into a directory on your system
2. Make sure the right Python packages are installed (opencv-python, opencv-contrib-python, picamera2, irc)
   If you do not have them, use the following commands in Linux:
   1. Python3.9 -m pip install opencv-python
   2. Python3.9 -m pip install opencv-contrib-python
   3. Python3.9 -m pip install picamera2
   4. Python3.9 -m pip install irc
3. To run in a virtual environment (when virtual environment folder):
   1. source myproject_env/bin/activate
   2. python3.9 irc_drone.py
4. To exit the virtual environment:
   1. Type ‘deactivate’
   2. To stop program either close the terminal, or hit CTRL + C on the terminal twice (we will fix this later)



## Detailed Code Description
The code creates two classes: UAVBot and UGVHitListener.

UAVBot is responsible for sending messages to an IRC channel. It connects to the IRC server, sets the connection status to False, and then connects to the channel. When the bot successfully joins the channel, it sets the connection status to True. It has a function send_fire_message which takes in the name of the team firing, the ArUco ID of the target, the time, and the location. It formats a message using these parameters and sends it to the channel using the privmsg function of the connection.

UGVHitListener is designed to listen to messages on the IRC channel and extract information from them. It connects to the same IRC server and channel as UAVBot. It also sets the connection status to False and then connects to the channel. When the bot successfully joins the channel, it sets the connection status to True. The function on_pubmsg is called when a message is posted in the channel. If the message contains the string _UGV_Hit_, the function parses the message, extracts the ArUco ID of the target, and saves it to the aruco_id variable.

The code is designed to detect ArUco markers in a video stream captured by a Raspberry Pi camera module and use the detected marker ID to trigger a drone-mounted laser. The code first sets up the 6x6_1000 ArUco marker dictionary and sets parameters for the marker detector. An instance of the ArUco detector is then created using the marker dictionary and parameters. The code then enters a loop where it continuously captures video frames from the camera and searches for ArUco markers.

If any markers are detected in a frame, their ID is extracted and added to a list of detected markers. The code then checks if the ID is already in the list and if not, logs a message to a file and turns on the laser using MAVLink commands.

The loop runs while the drone is armed, the drone will loiter if a marker is detected. Once the drone loiters over the marker it shoots an LED laser at the UGV receiver and then receives the hit confirmation from UGV through IRC communication. Once it gets the hit confirmation the drone will continue to look for other vehicles it has not received hit confirmations from.

In summary, this code is designed to detect specific ArUco markers in a video stream and use their detection to trigger a drone-mounted laser. The code logs a message to a file for each new marker detection, but does not log subsequent detections of the same marker ID.
