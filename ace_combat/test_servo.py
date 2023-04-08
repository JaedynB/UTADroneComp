from dronekit import connect, VehicleMode, LocationLocal
from pymavlink import mavutil
import time
import struct

from os import system
system('clear')

connection_string = '/dev/ttyUSB0'
############################### This will not work, the LED will be on through the range of 1110 to 1900+ ########################################

# print('Connecting to vehicle on: ', connection_string)
vehicle = connect(connection_string,baud=57600,wait_ready=True)
print('Connected')

# msg = vehicle.message_factory.command_long_encode(
#     0,0,
#     mavutil.mavlink.MAV_CMD_DO_SET_SERVO,0,
#     8,    # Channel
#     0,    # On/Off
#     0,0,0,0,0
# )
# vehicle.send_mavlink(msg)

# time.sleep(5)

# msg = vehicle.message_factory.command_long_encode(
#     0,0,
#     mavutil.mavlink.MAV_CMD_DO_SET_SERVO,0,
#     8,    # Channel
#     1,    # On/Off
#     0,0,0,0,0
# )
# vehicle.send_mavlink(msg)

print('on')
msg = vehicle.message_factory.command_long_encode(
    0,0,
    mavutil.mavlink.MAV_CMD_DO_SET_RELAY,0,
    0,    # Channel
    1, # PWM, between 1100 - 1900
    0,0,0,0,0       
)
vehicle.send_mavlink(msg)

time.sleep(5)

msg = vehicle.message_factory.command_long_encode(
    0,0,
    mavutil.mavlink.MAV_CMD_DO_SET_RELAY,0,
    0,    # Channel
    0, # PWM, between 1100 - 1900
    0,0,0,0,0       
)
vehicle.send_mavlink(msg)

print('off')



# vehicle.play_tune(bytes('C','utf-8'))

