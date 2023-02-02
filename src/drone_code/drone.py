# ~ from pymavlink import mavutil
# ~ import time
# ~ import sys

# ~ master = mavutil.mavlink_connection('/dev/ttyUSB0',baud=57600)

# ~ master.wait_heartbeat()

# ~ print("Heartbeat from system (system %u component %u)"%(master.target_system,master.target_component))


# ~ master.mav.command_long_send(master.target_system,master.target_component,
                            # ~ mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,0,1,1,0,0,0,0,0)

# ~ time.sleep(5)

# ~ master.mav.command_long_send(master.target_system,master.target_component,
                            # ~ mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,0,0,1,0,0,0,0,0)
from dronekit import connect, VehicleMode, LocationGlobalRelative, APIException
import time
import socket
# ~ import exceptions
import math
import argparse


vehicle = connect('/dev/ttyUSB0',baud=57600,wait_ready=True)

while vehicle.is_armable==False:
	print('waiting for arm')
	time.sleep(1)

vehicle.armed = True

while vehicle.armed==False:
	print('waitng')
	time.sleep(1)

print('armed')
