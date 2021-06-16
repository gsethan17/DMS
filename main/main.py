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

# from receive_data import receive_CAN, receive_video, receive_audio, receive_sensor
# from hmi import WindowClass
# # These variables are used in receive_data.py to sync threads
# TOTAL_THREADS_NUM = 4 ## Add 1 each time a sensor is added.
# thread_count = 0

def main():
    from receive_data import receive_CAN, receive_video, receive_audio, receive_sensor, WindowClass

    check_name = 'n'
    check_odd = 'n'
    start_flag = 'n'
    
    ### General setting ###
    # Read registered driver
    DRIVER_LIST = ["임세준", "오기성", "박중후", "김태산", "정의석"]    # [todo] read saved driver list
    DRIVER_NAME = "김태산"
    while check_name != 'y' :
        DRIVER_NAME = input("Enter your name : ")
        
        if str(DRIVER_NAME) in DRIVER_LIST:
            check_name = input("Are you registered driver, {}? [y/n]".format(str(DRIVER_NAME)))
        
        else :
            check_name = input("Are your new driver, {}? [y/n] ".format(str(DRIVER_NAME)))
            if check_name == 'y' :
                DRIVER_LIST.append(str(DRIVER_NAME))
                # [todo] save updated driver list
    
    while check_odd != 'y' :
        START_ODD = input("Enter current odd meter " )
        check_odd = input("Is current odd meter {}? [y/n] ".format(int(START_ODD)))
    #####################
        

    ###  CAN setting  ###
    
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

    myWindow = WindowClass(DRIVER_NAME)
    myWindow.show()
    
    ### Thread setting ###
    stop_threads = False
    workers = []
    data_names = ['CAN', 'video', 'audio', 'sensor']
    thread_functions = [receive_CAN, receive_video, receive_audio, receive_sensor]
    func_args = {'CAN': (),
                'video': (),
                'audio': (FORMAT, RATE, CHANNELS, CHUNK),
                'sensor': (),
                }
    #####################
    
    ### Driver's intention check ###
    while start_flag != 'y' :
        start_flag = input("Do you want to start collecting and storing data? [y/n] ")
    #####################
    
    print("Main thread started.")
    ### Thread generation ###
    print("Press 'Enter' if you want to terminate every processes.")
    for d_name, th_func in zip(data_names, thread_functions):
        worker = threading.Thread(target=th_func, args=(d_name, *func_args[d_name], lambda: stop_threads))
        workers.append(worker)
        worker.start()
    
    # thread terminate
    terminate_signal = input()
    while terminate_signal != '':
        print("Wrong input! Press 'Enter'")
        terminate_signal = input()
    stop_threads = True

    # thread terminate double check
    for worker in workers:
        worker.join()
    print("Main thread finished.")

    return terminate_signal
    #####################

    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    stop = main()
    app.exec_(stop)