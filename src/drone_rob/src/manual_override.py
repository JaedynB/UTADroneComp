import time
from   dronekit import connect, VehicleMode, LocationGlobalRelative

# Connect to the drone
vehicle = connect('/dev/ttyACM0', baud=57600, wait_ready=True)

# Function to handle manual override
def manual_override():
    print("Entering manual override...")

    # Change to GUIDED mode
    vehicle.mode  = VehicleMode("GUIDED")
    vehicle.armed = True
    vehicle.flush()

    while True:
        # Get user input for roll, pitch, yaw, and throttle
        roll     = float(input("Enter roll: "))
        pitch    = float(input("Enter pitch: "))
        yaw      = float(input("Enter yaw: "))
        throttle = float(input("Enter throttle: "))

        # Set the attitude and throttle
        vehicle.channels.overrides = {'1': roll, '2': pitch, '3': yaw, '4': throttle}

        # Check if user wants to exit manual override
        exit_override = input("Exit manual override? (y/n): ")
        if exit_override.lower() == 'y':
            break

    # Disarm the vehicle
    vehicle.armed = False
    vehicle.flush()
    print("Exited manual override.")

# Call the manual_override function
manual_override()

# Land the drone
vehicle.mode = VehicleMode("LAND")

# Wait until the drone has landed
while True:
    print("Vehicle mode: ", vehicle.mode.name)
    if vehicle.mode.name == 'LAND':
        print("Landed")
        break
    time.sleep(1)

# Disarm the vehicle
print("Disarming motors")
vehicle.armed = False
vehicle.close()