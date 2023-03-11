from   dronekit  import connect, VehicleMode, LocationGlobalRelative, APIException
from   picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
import time
from time import sleep
from datetime import datetime, timedelta
import cv2
from cv2 import aruco
import numpy     as np

###################################################################################
# This file requires the mission to have a return to launch/ landing waypoint
###################################################################################
connection_string = '/dev/ttyUSB0'

########################
# Aruco Marker
marker_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
param_markers = aruco.DetectorParameters_create()

cv2.startWindowThread()
picam2 = Picamera2()
###########################################
picam2.resolution = (640, 480)
#encoder = H264Encoder(bitrate=10000000)
#output = "test.h264"
#picam2.start_recording(encoder, output)
#time.sleep()
#picam2.stop_recording()

picam2.configure(picam2.create_video_configuration())

#picam2.resolution = (640, 480)
picam2.start_and_record_video("test.mp4")
#################################################

#picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
#picam2.start()
# A list for the IDs we find
markerID_list = []

file = open("log.txt","w")
file.write("============= BEGIN LOG =============\n")
########################


print('Connecting to vehicle on: ', connection_string)
vehicle = connect(connection_string,baud=57600,wait_ready=True)
print('Connected')

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
    vehicle.mode = VehicleMode("GUIDED")
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
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95: #Trigger just below target alt.
            print("Reached target altitude")
            break
        time.sleep(1)


#arm_and_takeoff(3)

print("Starting mission")
if vehicle.mode != 'STABILIZE':
    vehicle.wait_for_mode('STABILIZE')
    print('Mode: ', vehicle.mode)
#if vehicle.mode != 'AUTO':
#    vehicle.wait_for_mode('AUTO')
#    print('Mode: ', vehicle.mode)    


print('Arming...')
vehicle.arm()

if vehicle.armed == True:
    print('Armed')
else:
    print('Could not arm...')

# Aruco
while True:
    frame = picam2.capture_array()

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    (corners, ids, rejected) = aruco.detectMarkers(
        gray_frame, marker_dict, parameters=param_markers
    )
    
    if len(corners) > 0:
        
        ids = ids.flatten()
        
        for (markerCorner, markerID) in zip(corners, ids):
            corners = markerCorner.reshape((4, 2))
            (topLeft, topRight, bottomRight, bottomLeft) = corners
            
            topRight = (int(topRight[0]), int(topRight[1]))
            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
            bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
            topLeft = (int(topLeft[0]), int(topLeft[1]))
            
            # Draw
            cv2.line(frame, topLeft, topRight, (0, 255, 0), 2)
            cv2.line(frame, topRight, bottomRight, (0, 255, 0), 2)
            cv2.line(frame, bottomRight, bottomLeft, (0, 255, 0), 2)
            cv2.line(frame, bottomLeft, topLeft, (0, 255, 0), 2)
            
            # Computing and drawing the center of the ArUco marker
            cX = int((topLeft[0] + bottomRight[0]) / 2.0)
            cY = int((topLeft[1] + bottomRight[1]) / 2.0)
            #cv2.circle(frame, (cX, cY), 4, (0, 0, 255) -1)
            
            cv2.polylines(frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv2.LINE_AA)
            cv2.putText(frame, str(markerID), (topLeft[0], topLeft[1] - 15), cv2.FONT_HERSHEY_PLAIN, 1.6 , (200, 100, 0), 2, cv2.LINE_AA)
            #print("ID: {}".format(markerID))
            
            """
        
            # Draw the detected marker and print its ID
            cv2.polylines(frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv2.LINE_AA)
            cv2.putText(frame, f"ID: ", (corners[0][0], corners[0][1]), cv2.FONT_HERSHEY_PLAIN, 1.3, (200, 100, 0), 2, cv2.LINE_AA)
"""
            # Add marker ID to a list, check if ID in list, if in list do not log again
            if markerID not in markerID_list:
                #print("markerID: " + str(markerID))
                #print("markerID List: " + str(markerID_list))
                markerID_list.append(markerID)
                print("ID list: " + str(markerID_list))
                output = "ID: " + str(markerID) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")
            #print("markerID: " + str(markerID))
            #print("markerID List: " + str(markerID_list))
                
    cv2.imshow("Camera", frame)
    key = cv2.waitKey(25)
    
    """if key == ord("q"):
        break"""

file.write("============== END LOG ==============\n\n")
file.close()

#cv2.destroyAllWindows()
##############

vehicle.close()
picam2.stop_recording()
cv2.destroyAllWindows()
exit()

