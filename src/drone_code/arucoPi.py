import cv2
import time
import numpy as np
from cv2 import aruco
from picamera2 import Picamera2

marker_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
param_markers = aruco.DetectorParameters_create()

cv2.startWindowThread()
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
file = open("log.txt","a")
file.write("============= BEGIN LOG =============\n")
#time.sleep(.1)
while True:
    frame = picam2.capture_array()

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    marker_corners, marker_IDs, reject = aruco.detectMarkers(
        gray_frame, marker_dict, parameters=param_markers
    )
    
    if marker_corners:
        for ids, corners in zip(marker_IDs, marker_corners):
            cv2.polylines(
                frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv2.LINE_AA
            )
            corners = corners.reshape(4, 2)
            corners = corners.astype(int)
            top_left = (corners[0][0],corners[0][1])
            top_right = (corners[1][0],corners[1][1])
            bottom_right = (corners[2][0],corners[2][1])
            bottom_left = (corners[3][0],corners[3][1])
            cv2.putText(
                frame,
                f"ID: {ids[0]}",
                top_left,
                cv2.FONT_HERSHEY_PLAIN,
                1.3,
                (200, 100, 0),
                2,
                cv2.LINE_AA,
            )
            output = "ID: " + str(ids[0]) + "    TIME: " + str(time.strftime("%m-%d-%y  %I:%M:%S %p",time.localtime()))
            print(output)
            file.write(output + "\n")
    cv2.imshow("Camera", frame)
    key = cv2.waitKey(1)
    if key == ord("q"):
        break
file.write("============== END LOG ==============\n\n")
file.close()
cv2.destroyAllWindows()
