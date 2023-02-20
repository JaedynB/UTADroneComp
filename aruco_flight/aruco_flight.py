from   dronekit  import connect, VehicleMode, LocationGlobalRelative, APIException
from   picamera2 import Picamera2
import time
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

#cv2.startWindowThread()
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
# A list for the IDs we find
ids_list = []
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
    marker_corners, marker_IDs, reject = aruco.detectMarkers(
        gray_frame, marker_dict, parameters=param_markers
    )
    
    if marker_corners:
        for ids, corners in zip(marker_IDs, marker_corners):
            # Add marker ID to a list, check if ID in list, if in list do not log again
            if ids[0] not in ids_list:
                ids_list.append(ids[0])
                print("ID list: " + str(ids_list))
                output = "ID: " + str(ids[0]) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
                print(output)
                file.write(output + "\n")
                
    key = cv2.waitKey(45)

file.write("============== END LOG ==============\n\n")
file.close()

##############

vehicle.close()
#cv2.destroyAllWindows()
exit()
