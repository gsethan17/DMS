import threading
import cantools
import can
import pyaudio
import time
import sys
import pandas as pd
import os


from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic

def main():
    from receive_data import receive_CAN, receive_video, receive_audio, receive_sensor, WindowClass
    from check_status import check_driving_cycle, check_velocity, check_driver, check_odd
    
    ###  CAN setting  ###
    CAN_basePath = '/media/imlab/62C1-3A4A/CAN_dbc/20210527'
    P_db = cantools.database.load_file(CAN_basePath + '/AE_PE_2nd_Gen_2CH_P_CAN_KOOKMIN_20210527.dbc')
    C_db = cantools.database.load_file(CAN_basePath + '/AE_PE_2nd_Gen_2CH_C_CAN_KOOKMIN_20210527.dbc')
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
    DRIVER_LIST = ["임세준", "오기성", "박중후", "김태산", "정의석"]    # [todo] read saved driver list
    DRIVER_NAME = check_driver(DRIVER_LIST)

    
    ### START ODDMETRY CHECK ###
    START_ODD = check_odd()

    ### DATASET path setting ###
    DATASET_PATH = "../DMS_dataset/"
    if not os.path.isdir(DATASET_PATH + DRIVER_NAME):
        os.mkdir(DATASET_PATH + DRIVER_NAME)
    DATASET_PATH += (DRIVER_NAME + "/")
    
    if not os.path.isdir(DATASET_PATH + START_ODD):
        os.mkdir(DATASET_PATH + START_ODD)
    DATASET_PATH += START_ODD
    
    #####################    
    
    
    ### Thread setting ###
    stop_threads = False
    workers = []

    data_names = ['CAN', 'video', 'audio', 'sensor']
    thread_functions = [receive_CAN, receive_video, receive_audio, receive_sensor]
    func_args = {'CAN': (P_db, C_db, can_bus),
                'video': (),
                'audio': (FORMAT, RATE, CHANNELS, CHUNK),
                'sensor': (),
                }
    # data_names = ['CAN', 'audio', 'sensor']
    # thread_functions = [receive_CAN, receive_audio, receive_sensor]
    # func_args = {'CAN': (P_db, C_db, can_bus),
    #             # 'video': (),
    #             'audio': (FORMAT, RATE, CHANNELS, CHUNK),
    #             'sensor': (),
    #             }

    #####################
    
    ### Driver's intention check ###
    start_flag = 'n'
    while start_flag != 'y' :
        start_flag = input("[REQUEST] Do you want to start collecting and storing data? [y/n] ")
    #####################
    
    print("[INFO] Main thread started.")

    myWindow = WindowClass(DRIVER_NAME, DATASET_PATH)
    myWindow.show()
    
    ### Thread generation ###
    # print("[REQUEST] Press 'Enter' if you want to terminate every processes.")
    for d_name, th_func in zip(data_names, thread_functions):
        worker = threading.Thread(target=th_func, args=(d_name, DATASET_PATH, *func_args[d_name], lambda: stop_threads))
        workers.append(worker)
        worker.start()
    
    ### thread terminate ###
    time.sleep(5)
    terminate_signal = input("[REQUEST] Press 'Enter' if you want to terminate every processes.")
    while terminate_signal != '':
        print("[REQUEST] Wrong input! Press 'Enter'")
        terminate_signal = input()
    stop_threads = True

    ### thread terminate double check ###
    for worker in workers:
        worker.join()


    ### END ODDMETRY CHECK ###
    END_ODD = check_odd()

    odd_df = pd.DataFrame([(START_ODD, END_ODD)], columns=["START", "END"])
    odd_df.to_csv(f"{DATASET_PATH}/START_END_ODD.csv")
    
    
    
    print("[INFO] Main thread finished.")

    return terminate_signal
    #####################

    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    stop = main()
    QCoreApplication.instance().quit