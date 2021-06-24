import os
import sys
import time
import numpy as np

import pyaudio
import struct
from scipy.io.wavfile import write

def receive_audio(d_name="audio", FORMAT=pyaudio.paInt16, RATE=44100, CHANNELS=1, CHUNK=1024, stop=False):
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

if __name__=="__main__":
    receive_audio()