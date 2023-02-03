import time
from   dronekit import connect, VehicleMode

# Connect to the vehicle
vehicle = connect('/dev/ttyUSB0', baud = 57600, wait_ready = True)
print("Vehicle connected") # Check if vehicle is connected

while vehicle.is_armable == False:
    print('Waiting for arm checks to pass...')
    time.sleep(1)

# Change vehicle mode to GUIDED
vehicle.mode = VehicleMode("GUIDED")

# Arm the vehicle
vehicle.armed = True

# Wait for the vehicle to arm
while not vehicle.armed:
    print("Waiting for the drone to arm...")

# Takeoff to a specified altitude
vehicle.simple_takeoff(5) # Takeoff to 5 meters

# Wait until the drone reaches the target altitude
while True:
    print("Altitude: ", vehicle.location.global_relative_frame.alt)
    if vehicle.location.global_relative_frame.alt >= 20 * 0.95:
        print("Target altitude reached")
        break

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

# Disconnect the vehicle
vehicle.close()
