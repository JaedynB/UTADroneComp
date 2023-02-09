import asyncio
from mavsdk import System

async def run():
    # Connect to the drone
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyUSB0:57600")
    
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break
    
    # ~ print("Waiting for drone to have a global position estimate...")
    # ~ async for health in drone.telemetry.health():
        # ~ if health.is_global_position_ok and health.is_home_position_ok:
            # ~ print("-- Global position estimate OK")
            # ~ break
    
    # ~ print("Fetching amsl altitude at home location....")
    # ~ async for terrain_info in drone.telemetry.home():
        # ~ absolute_altitude = terrain_info.absolute_altitude_m
        # ~ break
    
    # ~ print("-- Downloading mission")
    # ~ mission_plan = await drone.mission.download_mission()
    
    # ~ print("-- Arming")
    # ~ await drone.action.arm()
    # ~ await asyncio.sleep(5)
    
    # ~ await drone.action.set_takeoff_altitude(10.0)
    
    # ~ await drone.param.set_param_float("MIS_TAKEOFF_ALT",20.0)
    
    # ~ alt = await drone.action.get_takeoff_altitude()
    # ~ print(alt)
    
    # ~ print("-- Taking off")
    # ~ await drone.action.takeoff()

    # ~ await asyncio.sleep(1)
    
    # To fly drone 20m above the ground plane
    # ~ flying_alt = absolute_altitude + 20.0
    # goto_location() takes Absolute MSL altitude
    # ~ await drone.action.goto_location(47.397606, 8.543060, flying_alt, 0)
    # ~ print(flying_alt)
    
    # ~ await asyncio.sleep(10)
    
    # ~ await drone.action.disarm()

    # ~ while True:
        # ~ print("Staying connected, press Ctrl-C to exit")
        # ~ await asyncio.sleep(1)

# Run the asyncio loop
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
