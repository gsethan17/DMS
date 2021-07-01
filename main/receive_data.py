# import threading
import multiprocessing
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
TOTAL_THREADS_NUM = multiprocessing.Value('d', 4) ### Add 1 each time a sensor is added. ###
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

def receive_CAN(d_name, DATASET_PATH, P_db, C_db, can_bus, stop_event):
    print(f"[INFO] '{d_name}' process is started.")

    CAN_PATH = DATASET_PATH + '/CAN/'
    if not os.path.isdir(CAN_PATH):
        os.mkdir(CAN_PATH)

    db_msg = []
    for msg in P_db.messages:
        if msg.name == 'CGW1':
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
    for msg in C_db.messages:
        if msg.name == 'NAVI_STD_SEG_E':
            db_msg.append(msg)
    
    df = pd.DataFrame(columns=['timestamp'])
    can_monitoring = {'ESP12': -1, 'SAS11': -1, 'WHL_SPD11': -1}

    cnt = 0
    first = True
    time_total = 0.
    cycle = 0
    sync_thread()
    print(f"[INFO] '{d_name}' process starts recording.")
    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    while(True):
        try:
            can_msg = can_bus.recv()
            st = time.time()
            for msg in db_msg:
                if can_msg.arbitration_id == msg.frame_id:
                    can_dict = P_db.decode_message(can_msg.arbitration_id, can_msg.data)
                    # can_dict['timestamp'] = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                    can_dict['timestamp'] = can_msg.timestamp
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
                    if msg.name == 'ESP12':
                        can_monitoring['ESP12'] = can_dict['CYL_PRES']
                    elif msg.name == 'SAS11':
                        can_monitoring['SAS11'] = can_dict['SAS_Angle']
                    elif msg.name == 'WHL_SPD11':
                        can_monitoring['WHL_SPD11'] = can_dict['WHL_SPD_FL']
            # print("CYL_PRES[{:08.5f}],  SAS_Angle[{:08.5f}],  WHL_SPD[{:08.5f}]".format(can_monitoring['ESP12'], can_monitoring['SAS11'], can_monitoring['WHL_SPD11']), end='\r')
            time_total += (time.time() - st)
            cycle += 1
        
            if stop_event.is_set():
                break
        
        except Exception as e:
            # pass
            # raise(e)
            if stop_event.is_set():
                break

    print(f"[INFO] # of CAN[{cnt}] MEAN_TIME[{time_total / cycle:.6f}] CYCLE[{cycle}]")
    print(f"[INFO] '{d_name}' process is terminated.")


def receive_video(d_name, DATASET_PATH, send_conn, stop_event):
    print(f"[INFO] '{d_name}' process is started.")

    VIDEO_PATH = DATASET_PATH + '/video/'
    if not os.path.isdir(VIDEO_PATH):
        os.mkdir(VIDEO_PATH)
    SIDE_VIDEO_PATH = VIDEO_PATH + 'SideView/'
    if not os.path.isdir(SIDE_VIDEO_PATH):
        os.mkdir(SIDE_VIDEO_PATH)
    FRONT_VIDEO_PATH = VIDEO_PATH + "FrontView/"
    if not os.path.isdir(FRONT_VIDEO_PATH):
        os.mkdir(FRONT_VIDEO_PATH)

    ### Configure depth and color streams... ###
    ### ...from Camera 1 ###
    pipeline_1 = rs.pipeline()
    config_1 = rs.config()
    config_1.enable_device("102422072555")
    config_1.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config_1.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config_1.enable_stream(rs.stream.infrared, 1, 640, 480, rs.format.y8, 30)

    ### ...from Camera 2 ###
    pipeline_2 = rs.pipeline()
    config_2 = rs.config()
    config_2.enable_device('043322071182')
    config_2.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config_2.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config_2.enable_stream(rs.stream.infrared, 2, 640, 480, rs.format.y8, 30)
    

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    colorVideo1 = cv2.VideoWriter(FRONT_VIDEO_PATH + 'color_front2.avi', fourcc, 30.0, (640,480))
    depthVideo1 = cv2.VideoWriter(FRONT_VIDEO_PATH + 'depth_front2.avi', fourcc, 30.0, (640,480))
    irVideo1 = cv2.VideoWriter(FRONT_VIDEO_PATH + 'ir_front2.avi', fourcc, 30.0, (640,480))

    colorVideo2 = cv2.VideoWriter(SIDE_VIDEO_PATH + 'color_side2.avi', fourcc, 30.0, (640,480))
    depthVideo2 = cv2.VideoWriter(SIDE_VIDEO_PATH + 'depth_side2.avi', fourcc, 30.0, (640,480))
    irVideo2 = cv2.VideoWriter(SIDE_VIDEO_PATH + 'ir_side2.avi', fourcc, 30.0, (640,480))


    ### Start streaming from both cameras ###
    pipeline_profile_1 = pipeline_1.start(config_1)
    # intr = pipeline_profile_1.as_video_stream_profile().get_intrinsics()
    # depth_sensor1 = pipeline_profile_1.get_device().first_depth_sensor()
    depth_sensor1 = pipeline_profile_1.get_device().query_sensors()[0]
    depth_sensor1.set_option(rs.option.enable_auto_exposure, True)
    

    # print("Depth Scale is: ", depth_scale)

    # clipping_distance_in_meters = 1
    # clipping_distance  = clipping_distance_in_meters/depth_scale


    align_to_color = rs.stream.color
    # align_to_depth = rs.stream.infrared
    align_color = rs.align(align_to_color)
    # align_depth = rs.align(align_to_depth)
    # infrared_scale = infrared_sensor.get_infrared_scale()
    # print("Infrared Scale is: ", infrared_scale)


    pipeline_profile_2 = pipeline_2.start(config_2)
    device2 = pipeline_profile_2.get_device()
    depth_sensor2 = device2.query_sensors()[0]
    depth_sensor2.set_option(rs.option.enable_auto_exposure, True)
    
    set_emitter = 0

    depth_sensor1.set_option(rs.option.emitter_enabled, set_emitter)
    # depth_sensor1.set_option(rs.option.visual_preset, 1)
    depth_sensor2.set_option(rs.option.emitter_enabled, set_emitter)
    # depth_sensor2.set_option(rs.option.visual_preset, 1)

    colorizer = rs.colorizer()
    colorizer.set_option(rs.option.visual_preset, 0)
    # colorizer.set_option(rs.option.histogram_equalizer_enabled, True)
    colorizer.set_option(rs.option.min_distance,0.7)
    colorizer.set_option(rs.option.max_distance, 4)

    colorizer1 = rs.colorizer()
    colorizer1.set_option(rs.option.histogram_equalization_enabled, True)
    colorizer1.set_option(rs.option.visual_preset, 0)
    # colorizer.set_option(rs.option.histogram_equalizer_enabled, True)
    colorizer1.set_option(rs.option.min_distance,0.01)
    colorizer1.set_option(rs.option.max_distance, 0.15)
            
    df = pd.DataFrame(columns=['timestamp'])
    df_flag = 1
    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))

    ### global lock ###
    sync_thread()
    print(f"[INFO] '{d_name}' process starts recording.")
    try:
        while True:
            
            ### Wait for a coherent pair of frames: depth and color ###
            df = df[0:0]
            
            frames_1 = pipeline_1.wait_for_frames()
            frames_2 = pipeline_2.wait_for_frames()
            
            df = df.append({'timestamp': time.time()}, ignore_index=True)
            if df_flag:
                df.to_csv(VIDEO_PATH + f"{start_time}.csv", mode='a', header=True, index=False)
                df_flag = 0
            else:
                df.to_csv(VIDEO_PATH + f"{start_time}.csv", mode='a', header=False, index=False)


            # frameset3 = align_depth.process(frames_1)
            # frameset2 = align_color.process(frames_1)
            # frameset = align_depth.process(frameset2)

            # color_frame_1 = frameset2.get_color_frame()

            ### Camera 1 ###
            color_frame_1 = frames_1.get_color_frame()
            # color_intr = color_frame_1.profile.as_video_stream_profile().intrinsics
            # print("=================")
            # print(color_intr)
            ir_frame_1 = frames_1.get_infrared_frame()
            # ir_intr = ir_frame_1.profile.as_video_stream_profile().intrinsics
            # print(ir_intr)
            depth_frame_1 = frames_1.get_depth_frame()
            # depth_intr = depth_frame_1.profile.as_video_stream_profile().intrinsics
            # print(depth_intr)

            

            if not depth_frame_1 or not color_frame_1 or not ir_frame_1:
                print("error")
                continue

            ### Convert images to numpy arrays ###
            depth_image_1 = np.asanyarray(colorizer.colorize(depth_frame_1).get_data())
            color_image_1 = np.asanyarray(color_frame_1.get_data())
            ir_image_1 = np.asanyarray(ir_frame_1.get_data())
            
            ### Apply colormap on depth image (image must be converted to 8-bit per pixel first) ###
            depth_colormap_1 = cv2.applyColorMap(cv2.convertScaleAbs(depth_image_1, alpha=1.0) , cv2.COLORMAP_JET)
            ir_img_1 = cv2.cvtColor(ir_image_1, cv2.COLOR_GRAY2BGR)
            
            ### Camera 2 ###
            # frames_2 = pipeline_2.wait_for_frames()
            depth_frame_2 = frames_2.get_depth_frame()
            color_frame_2 = frames_2.get_color_frame()
            ir_frame_2 = frames_2.get_infrared_frame()
            if not depth_frame_2 or not color_frame_2:
                continue
            
            ### Convert images to numpy arrays ###
            depth_image_2 = np.asanyarray(colorizer1.colorize(depth_frame_2).get_data())
            color_image_2 = np.asanyarray(color_frame_2.get_data())
            ir_image_2 = np.asanyarray(ir_frame_2.get_data())
            ir_img_2 = cv2.cvtColor(ir_image_2, cv2.COLOR_GRAY2BGR)

            ### Apply colormap on depth image (image must be converted to 8-bit per pixel first) ###
            depth_colormap_2 = cv2.applyColorMap(cv2.convertScaleAbs(depth_image_2, alpha=1.0), cv2.COLORMAP_JET)
    
            colorVideo1.write(color_image_1)
            depthVideo1.write(depth_colormap_1)
            irVideo1.write(ir_img_1)


            colorVideo2.write(color_image_2)
            depthVideo2.write(depth_colormap_2)
            irVideo2.write(ir_img_2)

            dp_color_1 = cv2.resize(color_image_1, (500,400))
            dp_color_2 = cv2.resize(color_image_2, (500,400))
            
            color_image_1 = cv2.resize(color_image_1, (450,350))
            color_image_2 = cv2.resize(color_image_2, (450,350))
            images1 = np.hstack((color_image_1, color_image_2))
            send_conn.send(images1)

            ### Stack all images horizontally ###
            # images1 = np.hstack((color_image_1, depth_colormap_1, ir_img_1))
            # images2 = np.hstack((color_image_2, depth_colormap_2, ir_img_2))
            
            ### Show images from both cameras ###

            # cv2.namedWindow("FRONT VIEW", cv2.WINDOW_AUTOSIZE)
            # time.sleep(1)
            # cv2.moveWindow("FRONT VIEW", 50, 0)
            # cv2.imshow("FRONT VIEW", dp_color_1)

            # cv2.namedWindow("SIDE VIEW", cv2.WINDOW_AUTOSIZE)
            # cv2.moveWindow("SIDE VIEW", 560, 0)
            # cv2.imshow("SIDE VIEW",  dp_color_2)
            # key = cv2.waitKey(10)
            
            if stop_event.is_set():
                break
    finally:

        ### Stop streaming ###
        pipeline_1.stop()
        pipeline_2.stop()

    print(f"[INFO] '{d_name}' process is terminated.")


def visualize_video(d_name, DATASET_PATH, recv_conn, stop_event):
    print(f"[INFO] '{d_name}' process is started.")
    sync_thread()
    
    while True:
        image = recv_conn.recv()
        # cv2.resize(image, (100,100))
        cv2.namedWindow("IMAGE MONITORING", cv2.WINDOW_AUTOSIZE)
        cv2.moveWindow("IMAGE MONITORING", 120, 1350)    
        cv2.imshow('IMAGE MONITORING', image)
        cv2.waitKey(1)

        if stop_event.is_set():
            cv2.destroyAllWindows()
            break
        
    print(f"[INFO] '{d_name}' process is terminated.")


def receive_audio(d_name, DATASET_PATH, FORMAT, RATE, CHANNELS, CHUNK, stop_event):
    print(f"[INFO] '{d_name}' process is started.")

    AUDIO_PATH = DATASET_PATH + '/audio/'
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
    
    df = pd.DataFrame(columns=['timestamp'])
    df_flag = 1

    sync_thread()
    print(f"[INFO] '{d_name}' process starts recording.")
    start_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
    while True:
        try:
            df = df[0:0]
            audio = stream.read(CHUNK)
            
            df = df.append({'timestamp': time.time()}, ignore_index=True)
            if df_flag:
                df.to_csv(AUDIO_PATH + f"{start_time}.csv", mode='a', header=True, index=False)
                df_flag = 0
            else:
                df.to_csv(AUDIO_PATH + f"{start_time}.csv", mode='a', header=False, index=False)

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

    print(f"[INFO] '{d_name}' process is terminated.")

def receive_sensor(d_name, DATASET_PATH, stop_event):
    sync_thread()
    pass


form_class = uic.loadUiType("../HMI/status.ui")[0]

class check_response(QDialog):
    def __init__(self, parent, DATASET_PATH):
        super(check_response, self).__init__(parent)
        self.parent = parent

        self.PATH = DATASET_PATH
        
        self.clicked_time = QTimer()
        self.clicked_time.setInterval(10000)
        self.replied_time = QTimer()
        self.replied_time.setInterval(300000)
        self.wav_in = '../HMI/in.wav'
        self.in_sound = AudioSegment.from_file(self.wav_in)

        check_response_ui = '../HMI/check.ui'
        uic.loadUi(check_response_ui, self)
        self.setWindowTitle('알림')

        if self.parent.re == 1:
            self.btn_re.setText(f'{parent.btn_1.text()}')
            self.btn_re.setStyleSheet("color: black;"
                                     "border-style: solid;"
                                     "border-width: 3px;"
                                     "background-color: #fa8d87;"
                                     "border-color: #f7453b;"
                                     "border-radius: 3px")
        elif self.parent.re == 2:
            self.btn_re.setText(f'{parent.btn_2.text()}')
            self.btn_re.setStyleSheet("color: black;"
                                     "border-style: solid;"
                                     "border-width: 3px;"
                                     "background-color: #fcdcae;"
                                     "border-color: #f79914;"
                                     "border-radius: 3px")
        elif self.parent.re == 3:
            self.btn_re.setText(f'{parent.btn_3.text()}')
            self.btn_re.setStyleSheet("color: black;"
                                     "border-style: solid;"
                                     "border-width: 3px;"
                                     "background-color: #87CEFA;"
                                     "border-color: #4a7ac2;"
                                     "border-radius: 3px")
        else:
            self.btn_re.setText(f'{parent.btn_4.text()}')
            self.btn_re.setStyleSheet("color: black;"
                                     "border-style: solid;"
                                     "border-width: 3px;"
                                     "background-color: #ebf0c0;"
                                     "border-color: #c4d900;"
                                     "border-radius: 3px")

        self.btn_re.setFont(QFont("Gulim",40))
        self.lbl_re.setStyleSheet("color: red;"
                                 "border-style: solid;"
                                 "border-width: 2px;"
                                 "background-color: #fcbdbd;"
                                 "border-color: #FA8072;"
                                 "border-radius: 3px")

        self.show()

        self.clicked_time.timeout.connect(self.record_csv)
        self.replied_time.timeout.connect(self.replied)
        self.btn_re.clicked.connect(self.btn)

        self.clicked_time.start()
        self.replied_time.start()

    def btn(self):
        self.clicked_time.stop()
        self.replied_time.stop()
        self.hide()
        playsound(self.wav_in)
        self.show_parent()

    def record_csv(self):
        self.clicked_time.stop()
        raw_data = [(time.time(), self.parent.name, self.parent.re)]
        data = pd.DataFrame(raw_data, columns=self.parent.df.columns)
        self.parent.df = self.parent.df.append(data)
        self.parent.df.to_csv(f'{self.PATH}', index=False, encoding='utf-8-sig')
        self.hide()

    def show_parent(self):
        self.parent.remind_time.start()
        self.parent.record_time.start()
        self.parent.show()

    def replied(self):
        self.replied_time.stop()
        playsound(self.wav_in)
        self.show_parent()
    
class WindowClass(QMainWindow, form_class):
    def __init__(self, DRIVER_NAME, DATASET_PATH):
        super().__init__()
        self.setupUi(self)
        self.name = DRIVER_NAME
        self.path = DATASET_PATH + "/HMI/"
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

        self.start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
        self.filename = self.start_time + '.csv'

        self.remind_time = QTimer()
        self.remind_time.setInterval(20000)
        self.record_time = QTimer()
        self.record_time.setInterval(40000)
        self.reshow_time = QTimer()
        self.reshow_time.setInterval(240000)
        print('show')
        self.setGeometry(0, 0, 1024, 1300)
        
        pal = QPalette()
        pal.setColor(QPalette.Background,QColor(255,255,255))
        self.lbl_driver.setFont(QFont("Gulim",44))
        self.setPalette(pal)

        if os.path.exists(self.path + self.filename):
            print(f'[INFO] {self.name} HMI starts recording.')
        else:
            df = pd.DataFrame(columns=['time', 'driver', 'status'])
            df.to_csv(self.path + self.filename, index=False)
            print(f'[INFO] {self.name} HMI file is created.')
        self.path = self.path + self.filename
        self.df = pd.read_csv(f'{self.path}', encoding='utf-8-sig')

        self.re = 0
        self.wav_out = '../HMI/out.wav'
        self.wav_in = '../HMI/in.wav'
        self.wav_no_answer = '../HMI/no_answer.wav'

        self.setWindowTitle('기록중')
        self.setWindowModality(2)
        self.show()
        self.lbl_driver.setText(self.name)
        pixmap = QPixmap('../HMI/캡처.PNG')
        self.lbl_image.setPixmap(QPixmap(pixmap))
        self.btn_1.clicked.connect(self.btn1)
        self.btn_2.clicked.connect(self.btn2)
        self.btn_3.clicked.connect(self.btn3)
        self.btn_4.clicked.connect(self.btn4)

        self.lbl_driver.setStyleSheet("color: black;"
                                      "border-style: solid;"
                                      "border-width: 3px;"
                                      "background-color: #87CEFA;"
                                      "border-color: #1E90FF;"
                                      "border-radius: 3px")
        self.btn_1.setStyleSheet("color: black;"
                                 "border-style: solid;"
                                 "border-width: 3px;"
                                 "background-color: #fa8d87;"
                                 "border-color: #f7453b;"
                                 "border-radius: 3px")
        self.btn_2.setStyleSheet("color: black;"
                                 "border-style: solid;"
                                 "border-width: 3px;"
                                 "background-color: #fcdcae;"
                                 "border-color: #f79914;"
                                 "border-radius: 3px")
        self.btn_3.setStyleSheet("color: black;"
                                 "border-style: solid;"
                                 "border-width: 3px;"
                                 "background-color: #87CEFA;"
                                 "border-color: #4a7ac2;"
                                 "border-radius: 3px")
        self.btn_4.setStyleSheet("color: black;"
                                 "border-style: solid;"
                                 "border-width: 3px;"
                                 "background-color: #ebf0c0;"
                                 "border-color: #c4d900;"
                                 "border-radius: 3px")

        self.remind_time.timeout.connect(self.remind)
        self.record_time.timeout.connect(self.record)
        self.reshow_time.timeout.connect(self.reshow)
        self.remind_time.start()
        self.record_time.start()
  
    def btn1(self):
        self.remind_time.stop()
        self.record_time.stop()
        self.re = 1
        self.hide()
        # os.system(self.wav_out)
        # play(self.out_sound)
        playsound(self.wav_out)
        # self.send_conn.send(self.wav_out)
        check_response(self, self.path)

    def btn2(self):
        self.remind_time.stop()
        self.record_time.stop()
        self.re = 2
        self.hide()
        # os.system(self.wav_out)
        # play(self.out_sound)
        playsound(self.wav_out)
        # self.send_conn.send(self.wav_out)
        check_response(self, self.path)

    def btn3(self):
        self.remind_time.stop()
        self.record_time.stop()
        self.re = 3
        self.hide()
        # os.system(self.wav_out)
        # play(self.out_sound)
        playsound(self.wav_out)
        # self.send_conn.send(self.wav_out)
        check_response(self, self.path)

    def btn4(self):
        self.remind_time.stop()
        self.record_time.stop()
        self.re = 4
        self.hide()
        # os.system(self.wav_out)
        # play(self.out_sound)
        playsound(self.wav_out)
        # self.send_conn.send(self.wav_out)
        check_response(self, self.path)

    def remind(self):
        self.remind_time.stop()
        playsound(self.wav_in)

    def record(self):
        self.record_time.stop()
        self.reshow_time.start()
        raw_data = [(time.time(), self.name, 0)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.path}', index=False, encoding='utf-8-sig')
        self.hide()
        playsound(self.wav_no_answer)

    def reshow(self):
        self.reshow_time.stop()
        self.remind_time.start()
        self.record_time.start()
        playsound(self.wav_in)
        self.show()


# def play_audio(d_name, recv_conn, stop_event):
#     print(f"[INFO] '{d_name}' process is started.")

#     while True:
#         wav = recv_conn.recv()
#         print(wav)
#         # playsound(wav)
#         if stop_event.is_set():
#             break

#     print(f"[INFO] '{d_name}' process is terminated.")

# def receive_HMI(d_name, DATASET_PATH, DRIVER_NAME, stop_event):
#     print(f"[INFO] '{d_name}' process is started.")

#     sync_thread()

#     playsound("../HMI/in.wav")
#     myWindow = WindowClass(DRIVER_NAME, DATASET_PATH)
#     myWindow.show()

#     while True:
#         if stop_event.is_set():
#             QCoreApplication.instance().quit
#             break

#     print(f"[INFO] '{d_name}' process is terminated.")
    
#     return