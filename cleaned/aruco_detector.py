from   dronekit  import connect, VehicleMode
from   picamera2 import Picamera2
from   pymavlink import mavutil
from   cv2       import aruco
import numpy     as np
import datetime  as dt
import cv2
import time
import logging

class ArUcoDetector:
    def __init__(self):
        self.marker_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000)    # Load the 6x6 ArUco marker dictionary with 1000 markers
        self.param_markers = cv2.aruco.DetectorParameters()                                # Set the parameters for the marker detector
        self.detector      = cv2.aruco.ArucoDetector(self.marker_dict, self.param_markers) # Create an instance of the ArUco detector using the marker dictionary and parameters

    def detect_markers(self, frame):
        frame      = picam2.capture_array()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # corners  - A list of detected marker corners, where each element is an array of four corner points in pixel coordinates
        # ids      - A list of detected marker IDs, where each element corresponds to the marker at the corresponding index in the corners list
        # rejected - A list of rejected candidate marker corners that did not meet the detection criteria
        (corners, ids, rejected) = aruco.detectMarkers(
            gray_frame,                      # The input grayscale image in which the markers will be detected
            self.marker_dict,                # The dictionary of markers used for detection
            parameters = self.param_markers  # Optional parameters for detection
        )
    
    def draw_markers(self, frame, corners, ids):
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

                    # Pull GPS Coordinates latitude and longitude from Mavlink stream
                    lat  = vehicle.location.global_relative_frame.lat
                    lon  = vehicle.location.global_relative_frame.lon

                    # Write GPS part of string message, convert GPS coords to strings so it can be encoded 
                    location     = str(lat) + '_' + str(lon)
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

                    ####vehicle.mode = VehicleMode("AUTO")
                    
        #cv2.imshow("Camera", frame)
        #key = cv2.waitKey(25)
        
        """
        if key == ord("q"):
            break
        """
