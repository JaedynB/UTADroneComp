import time
from   dronekit import connect, VehicleMode, LocationGlobalRelative

# Function to arm and takeoff the drone
def arm_and_takeoff(altitude):
    while not vehicle.is_armable:
        print("Waiting for vehicle to become armable...")
        time.sleep(1)

    print("Arming motors")
    vehicle.mode  = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print("Waiting for vehicle to arm...")
        time.sleep(1)

    print("Taking off")
    vehicle.simple_takeoff(altitude)

    while True:
        print("Altitude: ", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= altitude * 0.95:
            break
        time.sleep(1)

# Connect to the vehicle
vehicle = connect('/dev/ttyUSB0', baud = 57600, wait_ready = True)
print("Vehicle connected")

# Define the desired altitude (meters)
altitude = 4
arm_and_takeoff(altitude)

# Fly to a specified location
destination     = vehicle.location.global_relative_frame
destination.lat = 32.721946611134406
destination.lon = -97.12923351297042
vehicle.simple_goto(destination)

# Wait until the drone reaches the destination
while True:
    if vehicle.mode.name == 'GUIDED':
        remainingDistance = get_distance_metres(vehicle.location.global_frame, destination)
        print("Distance to target: ", remainingDistance)
        if remainingDistance <= 1:
            print("Reached target")
            break
    time.sleep(1)

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
