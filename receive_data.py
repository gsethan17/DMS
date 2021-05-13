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
    global thread_count, TOTAL_THREAD_NUM

    lock.acquire()
    try:
        thread_count += 1
    finally:
        lock.release()
    while thread_count != TOTAL_THREAD_NUM:
        pass

def receive_CAN(d_name, db, can_bus, stop):
    print(f"'{d_name}' thread started.")

    esp = sas = whl = 0.
    for message in db.messages:
        if message.name == 'ESP12':
            esp_frame_id = message.frame_id
        elif message.name == 'SAS11':
            sas_frame_id = message.frame_id
        elif message.name == 'WHL_SPD11':
            whl_frame_id = message.frame_id

    df = pd.DataFrame(columns=['timestamp'])

    sync_thread()

    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    while(True):
        try:
            message = can_bus.recv()
            if message.arbitration_id == esp_frame_id:
                # 210511: 추후 esp를 can_dict와 같은 일반화 변수로 변경하면 좋을 듯
                esp = db.decode_message(message.arbitration_id, message.data)
                esp['timestamp'] = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                df = df.append(esp, ignore_index=True)
            elif message.arbitration_id == sas_frame_id:
                sas = db.decode_message(message.arbitration_id, message.data)
                sas['timestamp'] = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                df = df.append(sas, ignore_index=True)
            elif message.arbitration_id == whl_frame_id:
                whl = db.decode_message(message.arbitration_id, message.data)
                whl['timestamp'] = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                df = df.append(whl, ignore_index=True)

            print("ESP: {:08.5f},  SAS: {:08.5f},  WHL: {:08.5f}".format(esp['CYL_PRES'], sas['SAS_Angle'], whl['WHL_SPD_FL']), end='\r')

            if stop():
                break
            
        except:
            # print("CAN failed.")
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


def receive_audio(d_name, FORMAT, RATE, CHANNELS, CHUNK, duration, stop):
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