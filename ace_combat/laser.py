from   dronekit           import connect, VehicleMode, LocationGlobalRelative, APIException
from   picamera2          import Picamera2
from   picamera2.encoders import H264Encoder, Quality
from   pymavlink          import mavutil
from   time               import sleep
from   datetime           import datetime, timedelta
from   cv2                import aruco
import numpy              as np
import time
import cv2
import logging

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

#cv2.startWindowThread()
picam2 = Picamera2(verbose_console=0)
picam2.configure(picam2.create_preview_configuration(main = {"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
#picam2.start_and_record_video("flight recording " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime())) + ".mp4")

connection_string = '/dev/ttyUSB0'

print('Connecting to vehicle on: ', connection_string)
vehicle = connect(connection_string,baud = 57600,wait_ready = True)
print('Connected')

"""print('Arming...')
vehicle.arm()
"""

if vehicle.armed == True:
    print('Armed')
else:
    print('Could not arm...')

file = open("log_marker_flight.txt","w")
file.write("============= BEGIN LOG =============\n")

# Aruco Marker
marker_dict   = aruco.Dictionary_get(aruco.DICT_4X4_50)
param_markers = aruco.DetectorParameters_create()

# A list for the IDs we find
markerID_list = []

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
            
            # Add marker ID to a list, check if ID in list, if in list do not log again
            if markerID not in markerID_list:
                
                #print("ID list: " + str(markerID_list))
                output = "Found ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")
                
                # Loiter drone if ID found
                vehicle.mode = VehicleMode("LOITER")
                #vehicle.wait_for_mode('LOITER')

                """
                Expect drone to identify the marker, then loiter in place for 10 seconds, before continuing on
                  through the rest of it's flight
                """
                time.sleep(10)
                
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
                time.sleep(0.25)

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
                
                vehicle.mode = VehicleMode("AUTO")

                markerID_list.append(markerID)
                
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
