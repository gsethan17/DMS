import threading
import time
import datetime as dt
import os
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import cantools
import can

import cv2

import pyaudio
import struct
from scipy.io.wavfile import write

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from playsound import playsound

# These variables are used in receive_data.py to sync threads
TOTAL_THREADS_NUM = 4 ## Add 1 each time a sensor is added.
thread_count = 0

lock = threading.Lock()
def sync_thread():
    global thread_count, TOTAL_THREADS_NUM

    lock.acquire()
    try:
        thread_count += 1
    finally:
        lock.release()
    while thread_count != TOTAL_THREADS_NUM:
        pass

def receive_CAN(d_name, stop): # db, can_bus, stop):
    print(f"'{d_name}' thread started.")

    CAN_basePath = '/media/imlab/62C1-3A4A/CAN_dbc/20210527'
    C_db = cantools.database.load_file(CAN_basePath + '/AE_PE_2nd_Gen_2CH_C_CAN_KOOKMIN_20210527.dbc')
    P_db = cantools.database.load_file(CAN_basePath + '/AE_PE_2nd_Gen_2CH_P_CAN_KOOKMIN_20210527.dbc')
    can_bus = can.interface.Bus('can0', bustype='socketcan')
    db_msg = []
    for msg in P_db.messages:
        if msg.name == 'NAVI_STD_SEG_E':
            db_msg.append(msg)
        elif msg.name == 'CGW1':
            db_msg.append(msg)
        elif msg.name == 'EMS2':
            db_msg.append(msg)
        elif msg.name == 'EBS1':
            db_msg.append(msg)
        elif msg.name == 'ESP12':
            db_msg.append(msg)
        elif msg.name == 'SAS11':
            db_msg.append(msg)
        elif msg.name == 'WHL_SPD11':
            db_msg.append(msg)
        elif msg.name == 'HCU3':
            db_msg.append(msg)

    df = pd.DataFrame(columns=['timestamp'])
    can_monitoring = {'ESP12': -1, 'SAS11': -1, 'WHL_SPD11': -1}

    CAN_PATH = '../../DMS_dataset/can/'
    sync_thread()
    cnt = 0
    first = True
    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    while(True):
        try:
            can_msg = can_bus.recv()
            for msg in db_msg:
                if can_msg.arbitration_id == msg.frame_id:
                    print(msg.name)
                    can_dict = P_db.decode_message(can_msg.arbitration_id, can_msg.data)
                    can_dict['timestamp'] = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                    if len(df.columns) >= 48:
                        if first:
                            df.to_csv(CAN_PATH + f"{start_time}.csv", index=False)
                            first = False
                        else:
                            df.to_csv(CAN_PATH + f"{start_time}.csv", mode='a', header=False, index=False)
                        
                        cnt += 1
                        df = df[0:0]
                        df = df.append(can_dict, ignore_index=True)
                    else:
                        cnt += 1
                        df = df.append(can_dict, ignore_index=True)

                    # For monitoring
            #         if msg.name == 'ESP12':
            #             can_monitoring['ESP12'] = can_dict['CYL_PRES']
            #         elif msg.name == 'SAS11':
            #             can_monitoring['SAS11'] = can_dict['SAS_Angle']
            #         elif msg.name == 'WHL_SPD11':
            #             can_monitoring['WHL_SPD11'] = can_dict['WHL_SPD_FL']
            # print("ESP: {:08.5f},  SAS: {:08.5f},  WHL: {:08.5f}".format(can_monitoring['ESP12'], can_monitoring['SAS11'], can_monitoring['WHL_SPD11']), end='\r')

            if stop():
                break
        
        except Exception as e:
            # raise(e)
            if stop():
                break
    print(f"CAN COUNT[{cnt}]")
    print(f"'{d_name}' thread terminated.")


def receive_video(d_name, stop):
    print(f"'{d_name}' thread started.")

    x = dt.datetime.now()
    save_dir = '../../DMS_dataset/video/' + '{}_{}_{}_{}_{}'.format(x.year, x.month, x.day, x.hour, x.minute)

    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)
    else:
        pass

    past_cur_time = 0
    cap = cv2.VideoCapture(0)
    i=0

    sync_thread()

    while(cap.isOpened()):
        st_time = time.time()
        x_ = dt.datetime.now()
        cur_time = '{}_{}_{}'.format(x_.hour, x_.minute, x_.second)
        title = cur_time + '_' +str(i)

        if cur_time == past_cur_time:
            i+=1
        else:
            i=0

        ret, frame = cap.read()
        if ret:
            cv2.imshow('video_stream', frame)
            cv2.imwrite(save_dir+'/' + title + '.jpg', frame)
            past_cur_time = cur_time

            if stop():
                break

        else:
            print('Video receiving error.')

    cap.release()
    cv2.destroyAllWindows()
    print(f"'{d_name}' thread terminated.")


def receive_audio(d_name, FORMAT, RATE, CHANNELS, CHUNK, stop):
    print(f"'{d_name}' thread started.")

    p = pyaudio.PyAudio()
    stream = p.open(
            format = FORMAT,
            rate = RATE,
            channels = CHANNELS,
            input = True,
            frames_per_buffer = CHUNK
            )
    
    data = []
    flag = False

    sync_thread()

    start_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
    while True:
        try:
            frame = np.fromstring(stream.read(CHUNK), dtype = np.int16)

            if not flag : 
                data = frame
            else :
                data = np.concatenate((data, frame), axis = None)
            flag = True
            
            if stop():
                break

        except:
            if stop():
                break

    stream.stop_stream()
    stream.close()
    p.terminate()
    write(f"../../DMS_dataset/audio/{start_time}.wav", RATE, data.astype(np.int16))

    print(f"'{d_name}' thread terminated.")

def receive_sensor(d_name, stop):
    sync_thread()
    pass


form_class = uic.loadUiType("../HMI/status.ui")[0]

class WindowClass(QMainWindow, form_class) :
    def __init__(self, DRIVER_NAME):
        super().__init__()
        self.setupUi(self)
        self.name = DRIVER_NAME
        self.filename = self.name + '.csv'
        if os.path.exists(self.filename):
            print(f'{self.name} 기록 시작합니다')
        else:
            df = pd.DataFrame(columns=['time', 'driver', 'status'])
            df.to_csv(self.filename, index=False)
            print(f'{self.filename} 파일을 생성하였습니다')
        self.df = pd.read_csv(f'{self.name}.csv', encoding='utf-8-sig')
        self.setWindowTitle('기록중')
        self.setWindowModality(2)
        self.show()
        self.lbl_driver.setText(self.name)
        pixmap = QPixmap('../HMI/tempsnip.png')
        self.lbl_image.setPixmap(QPixmap(pixmap))
        self.btn_1.clicked.connect(self.btn1)
        self.btn_2.clicked.connect(self.btn2)
        self.btn_3.clicked.connect(self.btn3)

        self.lbl_driver.setStyleSheet("color: black;"
                                      "border-style: solid;"
                                      "border-width: 2px;"
                                      "background-color: #87CEFA;"
                                      "border-color: #1E90FF;"
                                      "border-radius: 3px")
        self.btn_1.setStyleSheet("color: white;"
                                 "border-style: solid;"
                                 "border-width: 2px;"
                                 "background-color: #f7453b;"
                                 "border-color: #f7453b;"
                                 "border-radius: 3px")
        self.btn_2.setStyleSheet("color: white;"
                                 "border-style: solid;"
                                 "border-width: 2px;"
                                 "background-color: #fcc82b;"
                                 "border-color: #fcc82b;"
                                 "border-radius: 3px")
        self.btn_3.setStyleSheet("color: white;"
                                 "border-style: solid;"
                                 "border-width: 2px;"
                                 "background-color: #4a7ac2;"
                                 "border-color: #4a7ac2;"
                                 "border-radius: 3px")

    def btn1(self):
        raw_data = [(time.time(), self.name, 1)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.alram()

    def btn2(self):
        raw_data = [(time.time(), self.name, 2)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.alram()

    def btn3(self):
        raw_data = [(time.time(), self.name, 3)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.name}.csv', index=False, encoding='utf-8-sig')
        self.alram()

    def alram(self):
        audio_in = '../HMI/in.mp3'
        audio_out = '../HMI/out.mp3'
        self.hide()
        self.setWindowTitle('알림')
        # playsound(audio_out)
        time.sleep(1)
        # playsound(audio_in)
        self.show()

