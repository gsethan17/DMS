from lib2to3.pgen2 import driver
import multiprocessing
from tracemalloc import start
import cantools
import can
import pyaudio
import time
import sys
import pandas as pd
import os
import configparser
from datetime import datetime, timedelta

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from playsound import playsound
from config import config

def main():
    from receive_data import receive_CAN, receive_video, visualize_video, receive_audio, WindowClass #, receive_HMI
    from receive_GNSS import receive_GNSS
    from check_status import check_driving_cycle, check_velocity, check_driver, check_odometer, check_intention, check_passenger, check_weight
    # from config import config

    # version = config['VERSION']['version']
    # save_path = config['PATH']['SAVE_PATH']
    # driver_list = eval(config['DRIVER']['driver_list'])

    start_time = time.time()

    version = config['VERSION']
    save_path = config['SAVE_PATH']
    driver_list = config['DRIVER_LIST']
    data_config = config['DATA']
    hmi_config = data_config['HMI']

    HMI_flag = config['DATA']['HMI']
    ###  CAN setting  ###
    CAN_flag = config['DATA']['CAN']
    CAN_basePath = os.path.join(save_path, 'dbc')
    P_db = cantools.database.load_file(os.path.join(CAN_basePath, 'P_CAN.dbc'))
    C_db = cantools.database.load_file(os.path.join(CAN_basePath, 'C_CAN.dbc'))
    can_bus = can.interface.Bus('can0', bustype='socketcan')
    print_can_status = config['CAN']['print_can_status']
    #####################


    ### Video setting ###
    frontView = config['DATA']['INSIDE_FRONT_CAMERA']
    sideView = config['DATA']['INSIDE_SIDE_CAMERA']
    #####################y


    ### Audio setting ###
    FORMAT = pyaudio.paInt16
    RATE = 44100
    CHANNELS = 1
    CHUNK = 1024
    #####################


    ### GNSS setting ###
    print_gnss_status = config['GNSS']['print_gnss_status']
    receive_trf_info = config['DATA']['TRAFFIC_INFO']
    #####################

    ### Driving cycle check ###
    check_driving_cycle(P_db, can_bus)
    time.sleep(0.5)


    ### Velocity status check ###
    # check_velocity(P_db, can_bus)
    time.sleep(0.5)


    ### DRIVER CHECK ###
    DRIVER_NAME = check_driver(driver_list)
    DRIVER_WEIGHT = check_weight()


    PASSENGER_WEIGHTS = check_passenger()

    ### START ODOMETRY CHECK ###
    START_ODO = check_odometer(C_db, can_bus)

    ### DATASET path setting ###

    DATASET_PATH = save_path + 'data/'
    # if not os.path.isdir(DATASET_PATH + DRIVER_NAME):
        # os.mkdir(DATASET_PATH + DRIVER_NAME)
    # DATASET_PATH += (DRIVER_NAME + "/")

    if not os.path.isdir(DATASET_PATH + START_ODO):
        os.makedirs(DATASET_PATH + START_ODO)
    DATASET_PATH += START_ODO
    #####################


    ### Multi-process setting ###
    procs = []
    stop_event = multiprocessing.Event()
    send_conn, recv_conn = multiprocessing.Pipe()

    data_names = ['CAN', 'audio', 'video', 'GNSS'] # 'video_visaulizer'
    proc_functions = [receive_CAN, receive_audio, receive_video, receive_GNSS] # visualize_video
    func_args = {'CAN': (P_db, C_db, can_bus, print_can_status),
                'video': (frontView, sideView, send_conn),
                'audio': (FORMAT, RATE, CHANNELS, CHUNK),
                'GNSS': (config, print_gnss_status, receive_trf_info),
                # 'video_visual': (recv_conn),
                }

    #####################

    ### Driver's intention check ###
    check_intention()

    #####################

    print("[INFO] Main thread started.")

    ### Process generation ###
    for d_name, proc_func in zip(data_names, proc_functions):
        if d_name != 'video':
            if not data_config[d_name]:
                continue
        else:
            if not frontView and not sideView:
                continue
        proc = multiprocessing.Process(target=proc_func, args=(d_name, DATASET_PATH, *func_args[d_name], stop_event))
        procs.append(proc)

    for proc in procs:
        proc.start()

    time.sleep(4)

    if hmi_config:
        playsound("../HMI/in.wav")
        myWindow = WindowClass(DRIVER_NAME, DATASET_PATH)
        myWindow.show()


    ### Process terminate ###
    terminate_signal = input("[REQUEST] Press 'Enter' if you want to terminate every processes.\n\n")
    while terminate_signal != '':
        print("[REQUEST] Invalid input! Press 'Enter'")
        terminate_signal = input()

    if hmi_config:
        QCoreApplication.instance().quit

    stop_event.set()

    ### thread terminate double check ###
    for proc in procs:
        proc.join()


    ### Velocity status check ###
    # check_velocity(P_db, can_bus)
    time.sleep(0.5)


    ### END ODOMETRY CHECK ###
    END_ODO = check_odometer(C_db, can_bus)
    odo_df = pd.DataFrame([(START_ODO, END_ODO, int(END_ODO) - int(START_ODO), version)], columns=["START", "END", "TOTAL", "VERSION"])
    odo_df.to_csv(f"{DATASET_PATH}/START_END_TOTAL_{int(END_ODO) - int(START_ODO)}km.csv")

    end_time = time.time()
    ########## UTC to KST ###########
    start_time = datetime.fromtimestamp(start_time)
    start_time_KST = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = datetime.fromtimestamp(end_time)
    end_time_KST = end_time.strftime('%Y-%m-%d %H:%M:%S')

    ###### to txt drivier info #########
    info_path = os.path.join(save_path, 'info.txt')

    f = open(info_path, 'a')
    string_time = start_time_KST
    ending_time = end_time_KST

    info = string_time+','
    info += ending_time+','
    info += str(START_ODO) + ','
    info += str(END_ODO) + ','
    info += DRIVER_NAME + ','
    info += str(DRIVER_WEIGHT) + ','
    for wei in PASSENGER_WEIGHTS:
        info += str(wei) + ','
    info += str(HMI_flag) + ','
    info += str(CAN_flag) + ','
    info += str(frontView) + ','
    info += str(sideView) + ','
    info += str(config['DATA']['audio']) + ','
    info += str(config['DATA']['GNSS']) + ','
    info += str(receive_trf_info) + '\n'

    f.write(info)
    f.close()

    # read

    # write (add)

    # save


    ###################################

    print("[INFO] Main process finished.")

    #####################


if __name__ == "__main__":
    # config = configparser.ConfigParser()
    # config.read('./config.ini')
    # from config import config

    if config['DATA']['HMI']:
        app = QApplication(sys.argv)
    main()
