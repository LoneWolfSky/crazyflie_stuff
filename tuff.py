import logging
import time
import sys
import keyboard

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils import uri_helper
from threading import Event

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

uri1 = uri_helper.uri_from_env(default = 'radio://0/80/2M/E7E7E7E808')

deck_attached_event = Event()

MotorPowerSetStr = "motorPower"

logging.basicConfig(level=logging.ERROR)

def simple_connect():
    print("Hello World!")
    time.sleep(3)
    print("Goodbye world ;(")

def actual_takeoff(scf):
    with MotionCommander(scf, default_height=0.5) as mc:
        time.sleep(3)
        mc.stop()

def param_stab_est_callback(name, value):
    print('The crazyflie has parameter ' + name + ' set at number: ' + value)

def simple_param_async(scf, groupstr, namestr):
    cf = scf.cf
    full_name = "motorPowerSet.m1"

    cf.param.add_update_callback(group=groupstr, name=namestr,
                                 cb=param_stab_est_callback)
    time.sleep(1)
    cf.param.set_value("motorPowerSet.enable", 1)
    time.sleep(1)
    cf.param.set_value(full_name, 64000)
    time.sleep(1)
    cf.param.set_value(full_name, 0)
    time.sleep(1)
    with MotionCommander(scf, 0.5) as mc:
        time.sleep(3)
        mc.land()

def flip(mc):
    mc.land()
    
def take_off_simple(scf):
    with MotionCommander(scf, default_height = 0.5) as mc:
        time.sleep(2)
        while(True):
            key_pressed = keyboard.read_key()
            match key_pressed:
                case 'w':
                    mc.start_forward()
                case 's':
                    mc.start_back()
                case 'l':
                    mc.land()
                case 'a':
                    mc.start_left()
                case 'd':
                    mc.start_right()
                case 'q':
                    mc.start_turn_left()
                case 'e':
                    mc.start_turn_right()
                case 'shift':
                    mc.start_up()
                case 'ctrl':
                    mc.start_down()
                case 'space':
                    mc.stop()
                case 'g':
                    flip(mc)
                case 'p':
                    break
            time.sleep(0.1)

def param_deck_flow(_, value_str):
    value = int(value_str)
    print(value)
    if value:
        deck_attached_event.set()
        print('Deck is attached!')
    else:
        print('Deck is NOT attached!')

def simple_log(scf, logconf):
    with SyncLogger(scf, lg_stab) as logger:

        for log_entry in logger:

            timestamp = log_entry[0]
            data = log_entry[1]
            logconf_name = log_entry[2]

            print('[%d][%s]: %s' % (timestamp, logconf_name, data))

            break

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    lg_stab = LogConfig(name='MotorPowerSet', period_in_ms=10)
    lg_stab.add_variable('motorPowerSet.m1', 'float')

    with SyncCrazyflie(uri1, cf=Crazyflie(rw_cache='./cache')) as scf:

        print("Check1")

        scf.cf.param.add_update_callback(group="deck", name="bcFlow2",
                                cb=param_deck_flow)
        time.sleep(1)

        print("check2")

        if not deck_attached_event.wait(timeout=5):
            print('No flow deck detected!')
            sys.exit(1)

        # Arm the Crazyflie
        scf.cf.platform.send_arming_request(True)
        time.sleep(1.0)

        print("check3")

        #take_off_simple(scf)

        #actual_takeoff(scf)
        
        simple_param_async(scf, "skbidi", "toilet")
