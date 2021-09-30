import multiprocessing
import cantools
import can
import pyaudio
import time
import sys
import pandas as pd
import os
import configparser

def main(save_path, version):
    from tmp_receive_data import receive_audio
    from tmp_check_status import check_driver, check_odometer
    
    ###  CAN setting  ###
    CAN_basePath = os.path.join(save_path, 'dbc')
    P_db = cantools.database.load_file(os.path.join(CAN_basePath, 'P_CAN.dbc'))
    # C_db = cantools.database.load_file(CAN_basePath + '/AE_PE_2nd_Gen_2CH_C_CAN_KOOKMIN_20210527.dbc')
    C_db = cantools.database.load_file(os.path.join(CAN_basePath, 'C_CAN.dbc'))
    can_bus = can.interface.Bus('can0', bustype='socketcan')
    #####################

    ### Audio setting ###
    FORMAT = pyaudio.paInt16
    RATE = 44100
    CHANNELS = 1
    CHUNK = 1024
    #####################

    ### DRIVER CHECK ###
    DRIVER_LIST = ["오기성", "박중후", "김태산", "정의석"]    # [todo] read saved driver list
    DRIVER_NAME = check_driver(DRIVER_LIST)

    ### START ODOMETRY CHECK ###
    START_ODO = check_odometer(C_db, can_bus)

    ### DATASET path setting ###
    DATASET_PATH = save_path
    if not os.path.isdir(DATASET_PATH + DRIVER_NAME):
        os.mkdir(DATASET_PATH + DRIVER_NAME)
    DATASET_PATH += (DRIVER_NAME + "/")
    
    if not os.path.isdir(DATASET_PATH + START_ODO):
        os.mkdir(DATASET_PATH + START_ODO)
    DATASET_PATH += START_ODO
    
    #####################    
    
    
    ### Process setting ###
    procs = []
    stop_event = multiprocessing.Event()

    data_names = ['audio']
    proc_functions = [receive_audio]
    func_args = {
                'audio': (FORMAT, RATE, CHANNELS, CHUNK),
                }

    #####################
    
    print("[INFO] Main thread started.")

    ### Process generation ###
    for d_name, proc_func in zip(data_names, proc_functions):
        proc = multiprocessing.Process(target=proc_func, args=(d_name, DATASET_PATH, *func_args[d_name], stop_event))
        procs.append(proc)
    
    for proc in procs:
        proc.start()

    ### Process terminate ###
    time.sleep(4)

    terminate_signal = input("[REQUEST] Press 'Enter' if you want to terminate every processes.\n\n")
    while terminate_signal != '':
        print("[REQUEST] Invalid input! Press 'Enter'")
        terminate_signal = input()
    stop_event.set()

    ### thread terminate double check ###
    for proc in procs:
        proc.join()

    print("[INFO] Main process finished.")

    #####################

    
if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('./config.ini')

    VERSION = config['VERSION']['version']
    SAVE_PATH = config['PATH']['SAVE_PATH']

    main(SAVE_PATH, VERSION)