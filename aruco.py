# Install OpenCV on Windows:
# https://docs.opencv.org/4.x/d5/de5/tutorial_py_setup_in_windows.html

# See install for using aruco attribute
# https://stackoverflow.com/questions/45972357/python-opencv-aruco-no-module-named-cv-aruco
# Command: pip install opencv-contrib-python
import cv2 as cv
from cv2 import aruco
import numpy as np

marker_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)

param_markers = aruco.DetectorParameters_create()

cap = cv.VideoCapture(0)

file = open("log.txt","w")

while True:
    ret, frame = cap.read()
    
    if not ret:
        break
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    marker_corners, marker_IDs, reject = aruco.detectMarkers(gray_frame, marker_dict, parameters=param_markers)
    
    if marker_corners:
        for ids, corners in zip(marker_IDs, marker_corners):
            cv.polylines(frame, [corners.astype(np.int32)], True, (0, 255, 255), 4, cv.LINE_AA)
            corners      = corners.reshape(4, 2)
            corners      = corners.astype(int)
            top_right    = corners[0].ravel()
            top_left     = corners[1].ravel()
            bottom_right = corners[2].ravel()
            bottom_left  = corners[3].ravel()
            cv.putText(
                frame,
                f"ArUco ID: {ids[0]}",
                top_right,
                cv.FONT_HERSHEY_PLAIN,
                1.3,
                (200, 100, 0),
                2,
                cv.LINE_AA,
            )
            print(ids)
            file.write(str(ids)+"\n")
    cv.imshow("frame", frame)
    key = cv.waitKey(1)
    if key == ord("q"):
        break

file.close()
cap.release()
cv.destroyAllWindows()
