from main import TOTAL_THREADS_NUM, thread_count

import threading
import time
import numpy as np

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