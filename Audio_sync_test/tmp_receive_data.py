# import threading
import multiprocessing
from multiprocessing.process import parent_process
import time
import datetime as dt
import os
import sys
import socket
import pickle

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import cantools
import can

import cv2
import pyrealsense2 as rs

import pyaudio
import struct
from scipy.io.wavfile import write

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from playsound import playsound

from pydub import AudioSegment
from pydub.playback import play

### These variables are used in receive_data.py to sync threads ###
TOTAL_THREADS_NUM = multiprocessing.Value('d', 1) ### Add 1 each time a sensor is added. ###
thread_count = multiprocessing.Value('d', 0)

lock = multiprocessing.Lock()
def sync_thread():
    global thread_count, TOTAL_THREADS_NUM

    lock.acquire()
    try:
        thread_count.value += 1
    finally:
        lock.release()
        
    while thread_count.value != TOTAL_THREADS_NUM.value:
        pass
    return

def receive_audio(d_name, DATASET_PATH, FORMAT, RATE, CHANNELS, CHUNK, stop_event):
    print(f"[INFO] pid[{os.getpid()}] '{d_name}' process is started.")

    AUDIO_PATH = DATASET_PATH + '/audio_sync_test/'
    if not os.path.isdir(AUDIO_PATH):
        os.mkdir(AUDIO_PATH)

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
    
    # df = pd.DataFrame(columns=['timestamp'])
    # df_flag = 1

    sync_thread()
    print(f"[INFO] '{d_name}' process starts recording.")
    start_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
    while True:
        try:
            # df = df[0:0]
            audio = stream.read(CHUNK)
            
            # df = df.append({'timestamp': time.time()}, ignore_index=True)
            # if df_flag:
            #     df.to_csv(AUDIO_PATH + f"{start_time}.csv", mode='a', header=True, index=False)
            #     df_flag = 0
            # else:
            #     df.to_csv(AUDIO_PATH + f"{start_time}.csv", mode='a', header=False, index=False)

            frame = np.fromstring(audio, dtype = np.int16)

            if not flag : 
                data = frame
            else :
                data = np.concatenate((data, frame), axis = None)
            flag = True
            
            if stop_event.is_set():
                break
                        
        except:
            if stop_event.is_set():
                break
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    write(f"{AUDIO_PATH + start_time}.wav", RATE, data.astype(np.int16))

    print(f"[INFO] pid[{os.getpid()}] '{d_name}' process is terminated.")
    return