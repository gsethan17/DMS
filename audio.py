import socket
import pyaudio
import numpy as np
import pickle
import struct
import matplotlib.pyplot as plt
from scipy.io.wavfile import write

def get_audio(FORMAT=pyaudio.paInt16, RATE = 44100, CHANNELS = 1, CHUNK = 1024, duration = 5) :
    
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

    for i in range(int(duration * RATE / CHUNK)) :
        frame = np.fromstring(stream.read(CHUNK), dtype = np.int16)

        if not flag : 
            data = frame

        else :
            data = np.concatenate((data, frame), axis = None)

        flag = True

    stream.stop_stream()
    stream.close()
    p.terminate()

    return data

def save_wav(data, save_path = './record.wav', RATE = 44100) : 
    write(save_path, RATE, data.astype(np.int16))


def audio_stream(host_ip, port, FORMAT=pyaudio.paInt16, RATE = 44100, CHANNELS = 1, CHUNK = 1024) :
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(client_socket)
    ipaddr = socket.gethostbyname(socket.gethostname())
    client_socket.bind(('192.168.35.141', 63331))
    print(client_socket)
    client_socket.connect((host_ip, port))
    connection = client_socket.makefile('wb')
    print("connect to 'server'")

    p = pyaudio.PyAudio()

    stream = p.open(
            format = FORMAT,
            rate = RATE,
            channels = CHANNELS,
            input = True,
            frames_per_buffer = CHUNK
            )
    
    while True :
        data = stream.read(CHUNK)
        wave = np.fromstring(data, dtype = np.int16)
        pic = pickle.dumps(data)
        size = len(pic)
        client_socket.sendall(struct.pack("Q", size) + pic)
        print('Sending data')

    # client_socket.close()


if __name__ == '__main__' :
    
#     audio_stream('113.198.211.159', 22222)
    data = get_audio()
    save_wav(data)
