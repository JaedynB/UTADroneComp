from   dronekit import connect
import logging
from   aruco_detector import ArUcoDetector

def initialize():
    """
    Attempt to stop the Pi Camera debug error from coming up
        If the debug errors still show up, remove everything from this block and
        only keep logging.basicConfig(filename = 'debug.log', level = logging.INFO)
    """
    console_handler = logging.StreamHandler()       # Create a logging handler that logs warnings and above to the console
    console_handler.setLevel(logging.WARNING)
    logging.getLogger().addHandler(console_handler) # Add the console logging handler to the root logger
    logging.getLogger().setLevel(logging.WARNING)   # Set the root logger's level to warnings and above

    # Start a video recording and saving it to a file with a name based on the current time stamp
    #picam2.start_and_record_video("flight recording " + str(time.strftime("%m-%d-%y  %I:%M:%S %p", time.localtime())) + ".mp4")

    print("Creating the IRC bots...")

    # Create and start the UAVBot in a separate thread
    uav_bot    = UAVBot()
    uav_thread = threading.Thread(target = run_bot, args = (uav_bot,))
    uav_thread.start()

    # Create and start the UGVHitListener in a separate thread
    listener        = UGVHitListener()
    listener_thread = threading.Thread(target = run_bot, args = (listener,))
    listener_thread.start()

    # Wait for the UAVBot and UGVHitListener to connect to the server
    while not uav_bot.connected and not listener.connected:
        time.sleep(1)

    # Set the connection string to the USB port that the drone is connected to
    connection_string = '/dev/ttyUSB0'

    print('Connecting to vehicle on: ', connection_string)

    # Connect to the drone with the specified connection string and baud rate
    #   Wait until the drone is ready before continuing
    vehicle = connect(connection_string,baud = 57600, wait_ready = True)

    # Print a message indicating that the program has successfully connected to the drone
    print('Connected')

    # Arm the drone
    print('Arming...')
    vehicle.arm()

    # Check if the drone has been armed. If it has, print a message indicating that the drone has been armed
    #   If it has not, print a message indicating that the drone could not be armed
    if vehicle.armed == True:
        print('Armed')
    else:
        print('Could not arm...')

    file = open("log_marker_flight.txt","w")              # Create a new text file to log data to
    file.write("============= BEGIN LOG =============\n") # Write a line to the file to indicate the start of the log

    """
    marker_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_1000) # Load the 6x6 ArUco marker dictionary with 1000 markers
    param_markers = cv2.aruco.DetectorParameters()                             # Set the parameters for the marker detector
    detector      = cv2.aruco.ArucoDetector(marker_dict, param_markers)        # Create an instance of the ArUco detector using the marker dictionary and parameters
    """
    
    # A list for the IDs we find
    markerID_list = []

    #arm_and_takeoff(3)

    print("Starting mission")

    if vehicle.mode != 'STABILIZE':
        vehicle.wait_for_mode('STABILIZE')
        print('Mode: ', vehicle.mode)

    """
    if vehicle.mode != 'AUTO':
        vehicle.wait_for_mode('AUTO')
        print('Mode: ', vehicle.mode)
    """

    print("\nNow looking for ArUco Markers...\n")

    return vehicle, detector