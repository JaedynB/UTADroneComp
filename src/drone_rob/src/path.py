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

# Fly the drone
print("Flying to the desired location")
vehicle.airspeed = 2
vehicle.simple_goto(vehicle.location.global_frame.lat + 0.001, vehicle.location.global_frame.lon + 0.001, altitude)

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
