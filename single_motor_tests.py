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
    with MotionCommander(scf, default_height=0.8) as mc:
        time.sleep(3)
        flip(mc)
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
    cf = scf.cf
    cf.param.set_value("motorPowerSet.enable", 1)
    cf.param.set_value("motorPowerSet.m1", 64000)
    cf.param.set_value("motorPowerSet.m2", 64000)
    cf.param.set_value("motorPowerSet.m3", 64000)
    cf.param.set_value("motorPowerSet.m4", 64000)
    time.sleep(0.5)
    cf.param.set_value("motorPowerSet.enable", 0)
    time.sleep(3)

#this is a comment
    
def take_off_simple(scf, logconf):
    mc = MotionCommander(scf)
    mc.take_off(.5,.5)
    time.sleep(2)
    cf = scf.cf
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()
    while(True):
        key_pressed = keyboard.read_key()
        match key_pressed:
            case 'w':
                mc.start_forward(.5)
            case 's':
                mc.start_back(.5)
            case 'l':
                mc.land()
            case 'a':
                mc.start_left(.5)
            case 'd':
                mc.start_right(.5)
            case 'q':
                mc.start_turn_left(45)
            case 'e':
                mc.start_turn_right(45)
            case 'shift':
                mc.start_up(.5)
            case 'ctrl':
                mc.start_down(.5)
            case 'g':
                flip(mc)
            case 'p':
                logconf.stop()
                break
            case 'space':
                mc.stop()
        time.sleep(0.1)
        print(key_pressed)

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

            #timestamp = log_entry[0]
            data = log_entry[1]
            #logconf_name = log_entry[2]

            print(data)

            break

def log_stab_callback(timestamp, data, logconf):
    if timestamp // 10 % 10 == 0:
        print('[%d][%s]: %s' % (timestamp, logconf.name, data))

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    lg_stab = LogConfig(name='MotorPowerSet', period_in_ms=10)
    lg_stab.add_variable('motorPowerSet.m1', 'float')

    lg_zrange = LogConfig(name = "Range", period_in_ms=10)
    lg_zrange.add_variable('range.zrange', 'FP16')

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

        take_off_simple(scf, lg_zrange)

        #actual_takeoff(scf)
        
        #simple_param_async(scf, "skbidi", "toilet")
