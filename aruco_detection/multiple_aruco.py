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
ids_list = []

file = open("log.txt","w")
file.write("============= BEGIN LOG =============\n")
#time.sleep(.1)
while True:
    frame = picam2.capture_array()

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    marker_corners, marker_IDs, reject = aruco.detectMarkers(
        gray_frame, marker_dict, parameters=param_markers
    )
    
if marker_corners:
    for i in range(len(marker_corners)):
        corners = marker_corners[i].reshape(4, 2)
        corners = corners.astype(int)
        ids = marker_IDs[i]
        
        # Draw the detected marker and print its ID
        cv2.polylines(frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv2.LINE_AA)
        cv2.putText(frame, f"ID: {ids[i]}", (corners[0][0], corners[0][1]), cv2.FONT_HERSHEY_PLAIN, 1.3, (200, 100, 0), 2, cv2.LINE_AA)

        # Add marker ID to a list, check if ID in list, if in list do not log again
        if ids[i] not in ids_list:
            ids_list.append(ids[i])
            print("ID list: " + str(ids_list))
            output = "ID: " + str(ids[i]) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
            print(output)
            file.write(output + "\n")
                
    cv2.imshow("Camera", frame)
    key = cv2.waitKey(45)
    if key == ord("q"):
        break
file.write("============== END LOG ==============\n\n")
file.close()
cv2.destroyAllWindows()
