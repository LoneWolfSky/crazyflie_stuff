import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper

# URI to the Crazyflie to connect to
URI = uri_helper.uri_from_env(default = 'radio://0/80/2M/E7E7E7E808')

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

# Motion commander
mc = None

def simple_log(scf, logconf):
    with SyncLogger(scf, logconf) as logger:

        for log_entry in logger:

            timestamp = log_entry[0]
            data = log_entry[1]
            logconf_name = log_entry[2]

            print('[%d][%s]: %s' % (timestamp, logconf_name, data))

            break

# define deck 
deck_attached_event = Event()
def param_deck_flow(_, value_str):
    value = int(value_str)
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')

# Default height and position estimate
DEFAULT_HEIGHT = 0.5

# Define drone state
class State():
    def __init__(self):
        self.timestamp = 0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.yaw = 0.0
        self.d_left = 0.0
        self.d_right = 0.0
        self.d_front = 0.0
        self.d_back = 0.0
        self.d_bottom = 0.0

    def update(self, data: dict, timestamp: int = 0):
        self.timestamp = timestamp
        self.x = data['stateEstimate.x']
        self.y = data['stateEstimate.y']
        self.z = data['stateEstimate.z']
        self.yaw = data['stateEstimate.yaw']
        self.d_left = data['range.left']/1000
        self.d_right = data['range.right']/1000
        self.d_front = data['range.front']/1000
        self.d_back = data['range.back']/1000
        self.d_bottom = data['range.zrange']/1000

current_possition = State()

######## Define functions ######## 
def position_update_callback(timestamp, data, logconf):
    """
    Callback function for asynchronous logging
    """
    global current_possition
    current_possition.update(data, timestamp)


def custom_function(mc):
    mc.take_off(height=0.7, velocity=1)
    print("Hello")
    print("Let's get this bread")
    time.sleep(1)
    mc.forward(0.3,0.5)
    time.sleep(1)
    mc.right(current_possition.d_right - 0.2, 0.5)
    last3fwds = [0,0,0]
    for i in range(18):
        last3fwds[i%3] = current_possition.d_front
        mc.left(0.1, 0.5)
        print(last3fwds)
        time.sleep(.5)
        if(last3fwds[0] == last3fwds[1] == last3fwds[2] == 16.384):
            mc.right(0.1)
            break
    mc.forward(3.7, .75)
    loc = [1, 1.45] #this is what the fwd and right readings should be in a perfect world
    actLoc = [current_possition.d_front, current_possition.d_right] # this is the drone's current values for those readings
    print("+Left/-Right: ", loc[1] - actLoc[1], "\n+Fwd/-Bck: ", loc[0] - actLoc[0])
    mc.move_distance(loc[0] - actLoc[0], loc[1] - actLoc[1], 0, 0.5)
    mc.land()


######### Start Program ###########
if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        # Check the deck 
        scf.cf.param.add_update_callback(group='deck', name='bcFlow2',
                                         cb=param_deck_flow)
        time.sleep(1)
        
        # Define Log config
        logconf = LogConfig(name="Estimator", period_in_ms=10)
        logconf.add_variable('stateEstimate.x', 'FP16')
        logconf.add_variable('stateEstimate.y', 'FP16')
        logconf.add_variable('stateEstimate.z', 'FP16')
        logconf.add_variable('stateEstimate.yaw', 'FP16')
        logconf.add_variable('range.left', 'FP16')
        logconf.add_variable('range.right', 'FP16')
        logconf.add_variable('range.front', 'FP16')
        logconf.add_variable('range.back', 'FP16')
        logconf.add_variable('range.zrange', 'FP16')
        scf.cf.log.add_config(logconf)
        logconf.data_received_cb.add_callback(position_update_callback)

        # motion commander 
        mc = MotionCommander(scf, default_height=DEFAULT_HEIGHT)

        # Start the 
        logconf.start()
        
        
        custom_function(mc)

        
        logconf.stop()