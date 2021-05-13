from main import *
import threading
import time
import datetime as dt
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import cantools
import can

import cv2

import pyaudio
import struct
from scipy.io.wavfile import write

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

def receive_CAN(d_name, db, can_bus, stop):
    print(f"'{d_name}' thread started.")

    df = pd.DataFrame(columns=['timestamp'])
    can_monitoring = dict()

    sync_thread()

    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    while(True):
        try:
            can_msg = can_bus.recv()
            for db_msg in db.messages:
                if can_msg.arbitration_id == db_msg.frame_id:
                    can_dict = db.decode_message(can_msg.arbitration_id, can_msg.data)
                    can_dict['timestamp'] = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                    df = df.append(can_dict, ignore_index=True)

                    ## For monitoring
                    if db_msg.name == 'ESP12':
                        can_monitoring['ESP12'] = can_dict['CYL_PRES']
                    elif db_msg.name == 'SAS11':
                        can_monitoring['SAS11'] = can_dict['SAS_Angle']
                    elif db_msg.name == 'WHL_SPD11':
                        can_monitoring['WHL_SPD11'] = can_dict['WHL_SPD_FL']
            print("ESP: {:08.5f},  SAS: {:08.5f},  WHL: {:08.5f}".format(can_monitoring['ESP12'], can_monitoring['SAS11'], can_monitoring['WHL_SPD11']), end='\r')

            if stop():
                break
            
        except:
            if stop():
                break

    df.to_csv(f"../DMS_dataset/can/{start_time}.csv")
    print(f"'{d_name}' thread terminated.")


def receive_video(d_name, stop):
    print(f"'{d_name}' thread started.")

    x = dt.datetime.now()
    save_dir = '../DMS_dataset/video/' + '{}_{}_{}_{}_{}'.format(x.year, x.month, x.day, x.hour, x.minute)

    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)
    else:
        pass

    past_cur_time = 0
    cap = cv2.VideoCapture(0)
    i = 0

    sync_thread()

    while(cap.isOpened()):
        st_time = time.time()
        x_ = dt.datetime.now()
        cur_time = '{}_{}_{}'.format(x_.hour, x_.minute, x_.second)
        title = cur_time + '_' +str(i)

        if cur_time == past_cur_time:
            i += 1
        else:
            i = 0

        ret, frame = cap.read()
        if ret:
            cv2.imshow('video_stream', frame)
            cv2.imwrite(save_dir + '/' + title + '.jpg', frame)
            past_cur_time = cur_time
        else:
            print('Video receiving error.')
        
        if stop():
                break

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

    write(f"../DMS_dataset/audio/{start_time}.wav", RATE, data.astype(np.int16))
    print(f"'{d_name}' thread terminated.")