import multiprocessing
import cantools
import can
import pyaudio
import time
import sys
import pandas as pd
import os
import configparser


from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from playsound import playsound

def main(save_path, version):
    from receive_data import receive_CAN, receive_video, visualize_video, receive_audio, receive_sensor, WindowClass #, receive_HMI
    from check_status import check_driving_cycle, check_velocity, check_driver, check_odo, check_intention
    
    ###  CAN setting  ###
    CAN_basePath = os.path.join(save_path, 'dbc')
    P_db = cantools.database.load_file(os.path.join(CAN_basePath, 'P_CAN.dbc'))
    # C_db = cantools.database.load_file(CAN_basePath + '/AE_PE_2nd_Gen_2CH_C_CAN_KOOKMIN_20210527.dbc')
    C_db = cantools.database.load_file(os.path.join(CAN_basePath, 'C_CAN.dbc'))
    can_bus = can.interface.Bus('can0', bustype='socketcan')
    #####################


    ### Video setting ###
    
    #####################
    
    
    ### Audio setting ###
    FORMAT = pyaudio.paInt16
    RATE = 44100
    CHANNELS = 1
    CHUNK = 1024
    #####################
    
    
    ###  BIO setting  ###
    
    #####################
    
    
    ###  HMI setting  ###

    #####################


    ### Driving cycle check ###
    check_driving_cycle(P_db, can_bus)
    time.sleep(0.5)


    ### Velocity status check ###
    check_velocity(P_db, can_bus)
    time.sleep(0.5)
    

    ### DRIVER CHECK ###
    DRIVER_LIST = ["오기성", "박중후", "김태산", "정의석"]    # [todo] read saved driver list
    DRIVER_NAME = check_driver(DRIVER_LIST)

    
    ### START ODOMETRY CHECK ###
    START_ODO = check_odo()

    ### DATASET path setting ###
    # DATASET_PATH = "/media/imlab/62C1-3A4A/DMS_dataset_usb/"
    DATASET_PATH = save_path
    # DATASET_PATH = "../../test/dms_dataset/"
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
    send_conn, recv_conn = multiprocessing.Pipe()
    send_can, recv_can = multiprocessing.Pipe()
    # audio_send, audio_recv = multiprocessing.Pipe()

    # data_names = ['CAN', 'audio']#, 'HMI']#'video', 'video_visual', 'audio']#, 'sensor']
    data_names = ['audio']#, 'HMI']#'video', 'video_visual', 'audio']#, 'sensor']
    # proc_functions = [receive_CAN, receive_audio] #, receive_HMI]# receive_video, visualize_video, receive_audio]#, receive_sensor]
    proc_functions = [receive_audio] #, receive_HMI]# receive_video, visualize_video, receive_audio]#, receive_sensor]
    func_args = {#'CAN': (P_db, C_db, can_bus),
                # 'video': (send_conn),
                # 'video_visual': (recv_conn),
                'audio': (FORMAT, RATE, CHANNELS, CHUNK),
                # 'sensor': (),
                # 'HMI': [DRIVER_NAME],
                }

    #####################
    
    ### Driver's intention check ###
    check_intention()
    
    #####################
    
    print("[INFO] Main thread started.")
    

    ### Process generation ###
    for d_name, proc_func in zip(data_names, proc_functions):
        proc = multiprocessing.Process(target=proc_func, args=(d_name, DATASET_PATH, *func_args[d_name], stop_event))
        procs.append(proc)
    proc = multiprocessing.Process(target=receive_CAN, args=('CAN', DATASET_PATH, P_db, C_db, can_bus, send_can, stop_event))
    procs.append(proc)
    proc = multiprocessing.Process(target=receive_video, args=('video', DATASET_PATH, send_conn, stop_event))
    procs.append(proc)
    proc = multiprocessing.Process(target=visualize_video, args=('video_visual', DATASET_PATH, recv_conn, recv_can, stop_event))
    procs.append(proc)
    
    for proc in procs:
        proc.start()
    ### Process terminate ###
    time.sleep(4)

    # app = QApplication(sys.argv)
    playsound("../HMI/in.wav")
    myWindow = WindowClass(DRIVER_NAME, DATASET_PATH)
    myWindow.show()

    terminate_signal = input("[REQUEST] Press 'Enter' if you want to terminate every processes.\n\n")
    while terminate_signal != '':
        print("[REQUEST] Invalid input! Press 'Enter'")
        terminate_signal = input()
    QCoreApplication.instance().quit
    stop_event.set()

    # QCoreApplication.instance().quit    

    ### thread terminate double check ###
    for proc in procs:
        proc.join()


    ### Velocity status check ###
    check_velocity(P_db, can_bus)
    time.sleep(0.5)


    ### END ODOMETRY CHECK ###
    END_ODO = check_odo()
    odo_df = pd.DataFrame([(START_ODO, END_ODO, int(END_ODO) - int(START_ODO), version)], columns=["START", "END", "TOTAL", "VERSION"])
    odo_df.to_csv(f"{DATASET_PATH}/START_END_TOTAL_{int(END_ODO) - int(START_ODO)}km.csv")
    
    
    print("[INFO] Main process finished.")

    #####################

    
if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('./config.ini')

    
    VERSION = config['VERSION']['version']
    SAVE_PATH = config['PATH']['SAVE_PATH']

    app = QApplication(sys.argv)
    main(SAVE_PATH, VERSION)
    # QCoreApplication.instance().quit
