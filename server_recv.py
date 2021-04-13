import struct
import pickle
import cv2
import numpy as np
import pandas as pd
from scipy.io.wavfile import write

def get_video_stream(conn):
    FILE_OUTPUT = 'log/video.avi'
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(FILE_OUTPUT, fourcc, 25.0,(640,480))
    data = b""
    payload_size = struct.calcsize(">L")
    # print("payload_size: {}".format(payload_size))
    while True:

        try:
            while len(data) < payload_size:
                # print("Recv: {}".format(len(data)))
                data += conn.recv(4096)

            # print("Done Recv: {}".format(len(data)))
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            # print("msg_size: {}".format(msg_size))
            while len(data) < msg_size:
                data += conn.recv(4096)
            frame_data = data[:msg_size]
             
            data = data[msg_size:]
            
            frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            #print(frame.shape)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            out.write(frame)
            #print(frame.shape)
            #cv2.imshow('ImageWindow', frame)
            #cv2.waitKey(1)

        except Exception as e:
            conn.close()
            break
    print("++++++++++++++++++++++++++++++++++++++")
    print("[INFO] Receiving Video Stream Finisehd")
    print("[INFO] Saved Video Stream")

def get_CAN_signal(conn):

    data1_list = []
    data2_list = []

    while True:

        try:
            data = conn.recv(7)
            received = str(data, encoding='utf-8')
            temp = received.split(" ")

            data1 = round(float(temp[0]),2)
            data2 = round(float(temp[1]),2)

            data1_list.append(data1)
            data2_list.append(data2)

           # print("Received: {} ,{}".format(data1, data2))

        except:
            conn.close()
            break
   
    print("++++++++++++++++++++++++++++++++++++")
    print("[INFO] Receiving CAN Signal Finished")
    dict = {"data1":data1_list, "data2":data2_list}
    recv_log = pd.DataFrame(dict)
    recv_log.to_csv("log/test_log.csv")
    print("[INFO] Complete Saving Received Data")


def get_MISC_signal(conn):
    while True:
        data = conn.recv(48)
        received = str(data, encoding='utf-8')
        print("received:", received)
        temp = received.split(" ")

        month = round(float(temp[0]),2)
        date  = round(float(temp[1]),2)
        hour = round(float(temp[2]),2)
        minute = round(float(temp[3]),2)
        sec = round(float(temp[4]),2)

        print("{}/{} {}:{}:{}".format(int(month),int(date),int(hour),int(minute),sec))


def get_audio_stream(conn) :
    FILE_OUTPUT = 'log/audio.wav'
    waves = []
    flag = False

    data = b""
    payload_size = struct.calcsize("Q")
    while True :
        try :
            while len(data) < payload_size:
                data += conn.recv(4096)

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size :
                data += conn.recv(4096)
            wave_data = data[:msg_size]
            data = data[msg_size:]
            #print(len(data))
            wave = pickle.loads(wave_data, fix_imports=True, encoding="bytes")

            if not flag :
                waves = wave

            else :
                waves = np.concatenate((waves, wave), axis = None)
            
            waves = np.fromstring(wave, dtype = np.int16)
            flag = True

            #print("received {} wavedata".format(len(wave)))
        
        except Exception as e:
            if flag :
                write(FILE_OUTPUT, 44100, wave)
            conn.close()
            break
    print("++++++++++++++++++++++++++++++++++++++")
    print("[INFO] Receiving Audio Stream Finisehd")
    print("[INFO] Saved Audio Stream")

