import cv2
import time
import numpy     as np
from   cv2       import aruco
from   picamera2 import Picamera2

marker_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
param_markers = aruco.DetectorParameters_create()

cv2.startWindowThread()
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# A list for the IDs we find
markerID_list = []

file = open("log.txt","w")
file.write("============= BEGIN LOG =============\n")
#time.sleep(.1)
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
    
    if key == ord("q"):
        break

file.write("============== END LOG ==============\n\n")
file.close()
cv2.destroyAllWindows()
