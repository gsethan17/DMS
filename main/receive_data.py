import multiprocessing
import time
import datetime as dt
import os
import pandas as pd
import numpy as np
import cv2
import pyrealsense2 as rs

import pyaudio
from scipy.io.wavfile import write
from tqdm import tqdm

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from playsound import playsound

from pydub import AudioSegment
from pydub.playback import play
from config import config

### These variables are used in receive_data.py to sync threads ###
data_config = config['DATA']
TOTAL_PROCESS_NUM = multiprocessing.Value('d', 0)
if data_config['CAN']:
    TOTAL_PROCESS_NUM.value += 1
if data_config['INSIDE_FRONT_CAMERA'] or data_config['INSIDE_SIDE_CAMERA']:
    TOTAL_PROCESS_NUM.value += 1
if data_config['audio']:
    TOTAL_PROCESS_NUM.value += 1

process_cnt = multiprocessing.Value('d', 0)

lock = multiprocessing.Lock()
def sync_process():
    global process_cnt, TOTAL_PROCESS_NUM

    lock.acquire()
    try:
        process_cnt.value += 1
    finally:
        lock.release()

    while process_cnt.value != TOTAL_PROCESS_NUM.value:
        pass


def receive_CAN(d_name, save_flag, DATASET_PATH, P_db, C_db, can_bus, print_status, stop_event):
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")

    CAN_PATH = DATASET_PATH + '/CAN/'
    if save_flag:
        if not os.path.isdir(CAN_PATH):
            os.mkdir(CAN_PATH)

    db_msg = []
    P_msg_name = []
    C_msg_name = []

    # P_msg_list = ['CGW1', 'EMS2', 'EBS1', 'ESP12', 'SAS11', 'WHL_SPD11', 'HCU3']
    C_msg_list = ['HEV_PC1', 'HEV_PC2', 'HEV_PC4', 'HEV_PC5','HEV_PC6', 'HEV_PC12', 'SAS11', 'ESP12', 'WHL_SPD11', 'CGW1', 'CLU12', 'CLU15']


    MSG_LENGTH = 0
    # for msg in P_db.messages:
    #     if msg.name in P_msg_list :
    #         db_msg.append(msg)
    #         P_msg_name.append(msg.name)
    #         MSG_LENGTH += len(msg.signals)
    for msg in C_db.messages:
        if msg.name in C_msg_list :
            db_msg.append(msg)
            C_msg_name.append(msg.name)
            MSG_LENGTH += len(msg.signals)

    C_signal_names = ['CF_Ems_EngStat', 'CR_Brk_StkDep_Pc', 'CR_Ems_AccPedDep_Pc', 'CR_Ems_EngSpd_rpm', 'CR_Ems_FueCon_uL', 'CR_Ems_VehSpd_Kmh', \
                    'CF_Tcu_TarGe', 'SAS_Angle', 'CYL_PRES', 'CYL_PRES_FLAG', 'LAT_ACCEL', 'LONG_ACCEL', 'YAW_RATE', \
                    'WHL_SPD_FL', 'WHL_SPD_FR', 'WHL_SPD_RL', 'WHL_SPD_RR', 'BAT_SOC', 'CF_Gway_HeadLampHigh', 'CF_Gway_HeadLampLow', \
                    'CR_Hcu_HigFueEff_Pc', 'CR_Hcu_NorFueEff_Pc', 'CF_Hcu_DriveMode', 'CR_Fatc_OutTempSns_C', 'CR_Hcu_EcoLvl', \
                    'CR_Hcu_FuelEco_MPG', 'CR_Hcu_HevMod', 'CF_Ems_BrkForAct', 'CR_Ems_EngColTemp_C', 'CF_Clu_InhibitD', 'CF_Clu_InhibitN', \
                    'CF_Clu_InhibitP', 'CF_Clu_InhibitR', 'CF_Clu_VehicleSpeed', 'CF_Clu_Odometer']

    ### timestamp : timestamp from CAN device
    ### timestamp2 : timestamp from PC
    timestamp_cols = ['timestamp', 'timestamp2']
    df = pd.DataFrame(columns=timestamp_cols)
    can_monitoring = {'ESP12': -1, 'SAS11': -1, 'WHL_SPD11': -1}
    cnt = 0
    first = True
    time_total = 0.
    cycle = 0
    # sync_process()
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process starts collecting.")
    st_time = time.time()
    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(st_time))
    while(True):
        try:
            can_msg = can_bus.recv()
            timestamp2 = time.time()
            st = time.time()
            for msg in db_msg:
                if can_msg.arbitration_id == msg.frame_id:
                    # if msg.name in P_msg_name :
                    #     can_dict = P_db.decode_message(can_msg.arbitration_id, can_msg.data)
                    # if msg.name in C_msg_name :
                    can_dict = C_db.decode_message(can_msg.arbitration_id, can_msg.data)
                    can_dict = {k: v for k, v in can_dict.items() if k in C_signal_names}
                    can_dict['timestamp'] = can_msg.timestamp
                    can_dict['timestamp2'] = timestamp2

                    if len(df.columns) >= len(C_signal_names) + len(timestamp_cols):
                        if save_flag:
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
                    if print_status:
                        if msg.name == 'ESP12':
                            can_monitoring['ESP12'] = can_dict['CYL_PRES']
                        elif msg.name == 'SAS11':
                            can_monitoring['SAS11'] = can_dict['SAS_Angle']
                        elif msg.name == 'WHL_SPD11':
                            can_monitoring['WHL_SPD11'] = can_dict['WHL_SPD_FL']
            if print_status:
                record_time = str(dt.timedelta(seconds=(st - st_time))).split(".")[0]
                print("[INFO] TIME[{}] WHL_SPD[{:7.2f}] CYL_PRES[{:7.2f}] SAS_Angle[{:7.2f}]".format(record_time, can_monitoring['WHL_SPD11'], can_monitoring['ESP12'], can_monitoring['SAS11']), end='\r')
            time_total += (time.time() - st)
            cycle += 1

            if stop_event.is_set():
                break

        except Exception as e:
            if stop_event.is_set():
                break

    print(f"[INFO] PID[{os.getpid()}] '{d_name}' # of CAN[{cnt}] MEAN_TIME[{time_total / cycle:.6f}] CYCLE[{cycle}]")
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")


def receive_video(d_name, save_flag, DATASET_PATH, frontView, sideView, send_conn, stop_event):
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")

    VIDEO_PATH = DATASET_PATH + '/video/internal/'
    if save_flag:
        if not os.path.isdir(VIDEO_PATH):
            os.makedirs(VIDEO_PATH)
        if sideView:
            SIDE_VIDEO_PATH = VIDEO_PATH + 'SideView/'
            if not os.path.isdir(SIDE_VIDEO_PATH):
                os.makedirs(SIDE_VIDEO_PATH)
        if frontView:
            FRONT_VIDEO_PATH = VIDEO_PATH + "FrontView/"
            if not os.path.isdir(FRONT_VIDEO_PATH):
                os.makedirs(FRONT_VIDEO_PATH)

    ### Configure depth and color streams... ###
    fps = 15

    ### ...from Camera 1 ###
    if frontView:
        pipeline_1 = rs.pipeline()
        config_1 = rs.config()

        config_1.enable_device("043322071182")
        config_1.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, fps)
        config_1.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, fps)
        config_1.enable_stream(rs.stream.infrared, 1, 1280, 720, rs.format.y8, fps)

    ### ...from Camera 2 ###
    if sideView:
        pipeline_2 = rs.pipeline()
        config_2 = rs.config()
        config_2.enable_device('102422072555')
        config_2.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, fps)
        config_2.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, fps)
        config_2.enable_stream(rs.stream.infrared, 1, 1280, 720, rs.format.y8, fps)


    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

    if frontView:
        colorVideo1 = cv2.VideoWriter(FRONT_VIDEO_PATH + 'color_front.avi', fourcc, float(fps), (1280, 720))
        # depthVideo1 = cv2.VideoWriter(FRONT_VIDEO_PATH + 'depth_front.avi', fourcc, float(fps), (1280, 720))
        irVideo1 = cv2.VideoWriter(FRONT_VIDEO_PATH + 'ir_front.avi', fourcc, float(fps), (1280, 720))

    if sideView:
        colorVideo2 = cv2.VideoWriter(SIDE_VIDEO_PATH + 'color_side.avi', fourcc, float(fps), (1280, 720))
        # depthVideo2 = cv2.VideoWriter(SIDE_VIDEO_PATH + 'depth_side.avi', fourcc, float(fps), (1280, 720))
        irVideo2 = cv2.VideoWriter(SIDE_VIDEO_PATH + 'ir_side.avi', fourcc, float(fps), (1280, 720))


    ### Start streaming from both cameras ###
    if frontView:
        pipeline_profile_1 = pipeline_1.start(config_1)
        depth_sensor1 = pipeline_profile_1.get_device().first_depth_sensor()
        depth_sensor1 = pipeline_profile_1.get_device().query_sensors()[0]
        depth_sensor1.set_option(rs.option.enable_auto_exposure, True)

    # clipping_distaynce_in_meterys = 1
    # clipping_distance  = clipping_distance_in_meters/depth_scale

    # align_to_color = rs.stream.color
    # align_to_depth = rs.stream.infrared
    # align_color = rs.align(align_to_color)
    # align_depth = rs.align(align_to_depth)
    # infrared_scale = infrared_sensor.get_infrared_scale()
    if sideView:
        pipeline_profile_2 = pipeline_2.start(config_2)
        depth_sensor2 = pipeline_profile_2.get_device().first_depth_sensor()
        depth_sensor2 = pipeline_profile_2.get_device().query_sensors()[0]
        # device2 = pipeline_profile_2.get_device()
        # depth_sensor2 = device2.query_sensors()[0]
        depth_sensor2.set_option(rs.option.enable_auto_exposure, True)

    set_emitter = 0
    if frontView:
        depth_sensor1.set_option(rs.option.emitter_enabled, set_emitter)
        depth_sensor1.set_option(rs.option.visual_preset, 2)
    if sideView:
        depth_sensor2.set_option(rs.option.emitter_enabled, set_emitter)
        depth_sensor2.set_option(rs.option.visual_preset, 2)

    colorizer1 = rs.colorizer()
    colorizer1.set_option(rs.option.visual_preset, 2)

    colorizer2 = rs.colorizer()
    colorizer2.set_option(rs.option.visual_preset, 2)

    df = pd.DataFrame(columns=['timestamp'])
    df_flag = True
    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))

    ### global lock ###
    # sync_process()
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process starts collecting.")
    try:
        while True:
            ### Wait for a coherent pair of frames: depth and color ###
            df = df[0:0]
            if frontView:
                frames_1 = pipeline_1.wait_for_frames()
            if sideView:
                frames_2 = pipeline_2.wait_for_frames()

            df = df.append({'timestamp': time.time()}, ignore_index=True)
            if df_flag:
                df.to_csv(VIDEO_PATH + f"{start_time}.csv", mode='a', header=True, index=False)
                df_flag = False
            else:
                df.to_csv(VIDEO_PATH + f"{start_time}.csv", mode='a', header=False, index=False)

            ### Camera 1 ###
            if frontView:
                color_frame_1 = frames_1.get_color_frame()
                ir_frame_1 = frames_1.get_infrared_frame()
                depth_frame_1 = frames_1.get_depth_frame()

                if not depth_frame_1 or not color_frame_1 or not ir_frame_1:
                    print("[INFO] VIDEO FRAME ERROR")
                    continue

                ### Convert images to numpy arrays ###
                depth_image_1 = np.asanyarray(colorizer1.colorize(depth_frame_1).get_data())
                color_image_1 = np.asanyarray(color_frame_1.get_data())
                ir_image_1 = np.asanyarray(ir_frame_1.get_data())

                ### Apply colormap on depth image (image must be converted to 8-bit per pixel first) ###
                # depth_colormap_1 = cv2.applyColorMap(depth_image_1 , cv2.COLORMAP_BONE)
                ir_image_1 = cv2.cvtColor(ir_image_1, cv2.COLOR_GRAY2BGR)

            ### Camera 2 ###
            if sideView:
                depth_frame_2 = frames_2.get_depth_frame()
                color_frame_2 = frames_2.get_color_frame()
                ir_frame_2 = frames_2.get_infrared_frame()
                if not depth_frame_2 or not color_frame_2 or not ir_frame_2:
                    print("[INFO] VIDEO FRAME ERROR")
                    continue

                ### Convert images to numpy arrays ###
                depth_image_2 = np.asanyarray(colorizer2.colorize(depth_frame_2).get_data())
                color_image_2 = np.asanyarray(color_frame_2.get_data())
                ir_image_2 = np.asanyarray(ir_frame_2.get_data())

                ### Apply colormap on depth image (image must be converted to 8-bit per pixel first) ###
                ir_image_2 = cv2.cvtColor(ir_image_2, cv2.COLOR_GRAY2BGR)

            if frontView:
                colorVideo1.write(color_image_1)
                # depthVideo1.write(depth_image_1)
                irVideo1.write(ir_image_1)

            if sideView:
                color_image_2 = np.flipud(color_image_2)
                ir_image_2 = np.flipud(ir_image_2)

                color_image_2 = np.fliplr(color_image_2)
                ir_image_2 = np.fliplr(ir_image_2)

                colorVideo2.write(color_image_2)
                # depthVideo2.write(depth_image_2)
                irVideo2.write(ir_image_2)

            ### Send image to visualizer process ###
            # dp_color_1 = cv2.resize(color_image_1, (500,400))
            # dp_color_2 = cv2.resize(color_image_2, (500,400))

            # if frontView:
            #     color_image_1 = cv2.resize(color_image_1, (450,350))
            #     ir_img_1 = cv2.resize(ir_img_1, (450, 350))
            #     images = np.hstack([color_image_1, ir_img_1])
            # if sideView:
            #     color_image_2 = cv2.resize(color_image_2, (450,350))
            #     images = np.hstack((color_image_1, color_image_2))

            # send_conn.send(images)
            ########################################

            if stop_event.is_set():
                break

    except Exception as e:
        print(e)
    finally:
        ### Stop streaming ###
        if frontView:
            pipeline_1.stop()
        if sideView:
            pipeline_2.stop()

    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")


def visualize_video(d_name, DATASET_PATH, recv_conn, stop_event):
    # print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")
    # sync_process()

    # while True:
    #     image = recv_conn.recv()
    #     # print(image.shape)
    #     # sas = recv_can.recv()
    #     # cv2.resize(image, (100,100))
    #     cv2.namedWindow("IMAGE MONITORING", cv2.WINDOW_AUTOSIZE)
    #     cv2.moveWindow("IMAGE MONITORING", 0, 1300)#0, 0, 1024, 1300)
    #     # cv2.putText(image, str(sas), (100, 100), cv2.FONT_HERSHEY_PLAIN, 7.0, (0,0,255), 2)
    #     cv2.imshow('IMAGE MONITORING', image)
    #     cv2.waitKey(1)

    #     if stop_event.is_set():
    #         cv2.destroyAllWindows()
    #         break

    # print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")
    pass


def receive_audio(d_name, save_flag, DATASET_PATH, FORMAT, RATE, CHANNELS, CHUNK, stop_event):
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")

    AUDIO_PATH = DATASET_PATH + '/audio/'
    if save_flag:
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

    # sync_process()
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process starts collecting.")
    start_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))

    dic = {}
    sub_count = 0
    max_count = 5000
    count = 0

    while True:
        try:
            df = df[0:0]
            audio = stream.read(CHUNK)

            df = df.append({'timestamp': time.time()}, ignore_index=True)
            if save_flag:
                if df_flag:
                    df.to_csv(AUDIO_PATH + f"{start_time}.csv", mode='a', header=True, index=False)
                    df_flag = 0
                else:
                    df.to_csv(AUDIO_PATH + f"{start_time}.csv", mode='a', header=False, index=False)

            frame = np.fromstring(audio, dtype = np.int16)

            sub_count += 1

            if not flag:
                data = frame
                flag = True
            else :
                if sub_count % max_count == 0:
                    dic[count] = data
                    count += 1
                    flag = False
                else :
                    data = np.concatenate((data, frame), axis = None)

            if stop_event.is_set():
                break

        except:
            if stop_event.is_set():
                break

    dic[count] = data
    stream.stop_stream()
    stream.close()
    p.terminate()

    key_flag = False
    print('[INFO] Saving audio data...')
    for key in tqdm(dic.keys()):
        if not key_flag :
            data = dic[key]
            key_flag = True
        else :
            data = np.concatenate((data, dic[key]), axis = None)

    if save_flag:
        write(f"{AUDIO_PATH + start_time}.wav", RATE, data.astype(np.int16))

    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")


form_class = uic.loadUiType("../HMI/status.ui")[0]
class check_response(QDialog):
    def __init__(self, parent, DATASET_PATH):
        super(check_response, self).__init__(parent)
        self.parent = parent

        self.PATH = DATASET_PATH

        self.clicked_time = QTimer()
        self.clicked_time.setInterval(10000)
        # self.replied_time = QTimer()
        # self.replied_time.setInterval(300000)
        # self.replied_time.setInterval(20000)
        self.wav_in = '../HMI/in.wav'
        self.in_sound = AudioSegment.from_file(self.wav_in)

        check_response_ui = '../HMI/check.ui'
        uic.loadUi(check_response_ui, self)
        self.setWindowTitle('알림')

        if self.parent.re == 1:
            self.btn_re.setStyleSheet(f"background-image: url(../HMI/{self.parent.re}.png);"
                                      "background-color: #FF816E;")
        elif self.parent.re == 2:
            self.btn_re.setStyleSheet(f"background-image: url(../HMI/{self.parent.re}.png);"
                                      "background-color: #FFBC8D;")
        elif self.parent.re == 3:
            self.btn_re.setStyleSheet(f"background-image: url(../HMI/{self.parent.re}.png);"
                                      "background-color: #C0E8FF;")
        else:
            self.btn_re.setStyleSheet(f"background-image: url(../HMI/{self.parent.re}.png);"
                                      "background-color: #FFEC95;")

        self.show()

        self.clicked_time.timeout.connect(self.record_csv)
        # self.replied_time.timeout.connect(self.replied)
        self.btn_re.clicked.connect(self.btn)

        self.clicked_time.start()
        # self.replied_time.start()

    def btn(self):
        self.clicked_time.stop()
        # self.replied_time.stop()
        self.hide()
        playsound(self.wav_in)
        self.parent.remind_time.start()
        self.parent.show()

    def record_csv(self):
        self.clicked_time.stop()
        raw_data = [(self.parent.time, self.parent.name, self.parent.re)]
        data = pd.DataFrame(raw_data, columns=self.parent.df.columns)
        self.parent.df = self.parent.df.append(data)
        self.parent.df.to_csv(f'{self.PATH}', index=False, encoding='utf-8-sig')
        self.hide()
        self.show_parent()

    def show_parent(self):
        self.parent.request_time.start()
        # self.parent.remind_time.start()
        # self.parent.record_time.start()
        self.parent.show()

    # def replied(self):
    #     self.replied_time.stop()
    #     playsound(self.wav_in)

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
        self.time = 0

        self.remind_time = QTimer()
        self.remind_time.setInterval(10000)
        # self.remind_time.setInterval(10000)
        self.record_time = QTimer()
        self.record_time.setInterval(10000)
        # self.record_time.setInterval(10000)
        self.reshow_time = QTimer()
        self.reshow_time.setInterval(40000)
        # self.reshow_time.setInterval(20000)
        self.request_time = QTimer()
        # self.reshow_time.setInterval(240000)
        self.request_time.setInterval(50000)
        self.setGeometry(0, 0, 1024, 1300)

        pal = QPalette()
        pal.setColor(QPalette.Background,QColor(45, 45, 45))
        opacity_effect1 = QGraphicsOpacityEffect(self.btn_1)
        opacity_effect1.setOpacity(0)
        self.btn_1.setGraphicsEffect(opacity_effect1)
        opacity_effect2 = QGraphicsOpacityEffect(self.btn_2)
        opacity_effect2.setOpacity(0)
        self.btn_2.setGraphicsEffect(opacity_effect2)
        opacity_effect3 = QGraphicsOpacityEffect(self.btn_3)
        opacity_effect3.setOpacity(0)
        self.btn_3.setGraphicsEffect(opacity_effect3)
        opacity_effect4 = QGraphicsOpacityEffect(self.btn_4)
        opacity_effect4.setOpacity(0)
        self.btn_4.setGraphicsEffect(opacity_effect4)
        self.setPalette(pal)

        if os.path.exists(self.path + self.filename):
            print(f'[INFO] {self.name} HMI starts collecting.')
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
        pixmap = QPixmap('../HMI/status.png')
        self.lbl_image.setPixmap(QPixmap(pixmap))
        self.btn_1.clicked.connect(self.btn1)
        self.btn_2.clicked.connect(self.btn2)
        self.btn_3.clicked.connect(self.btn3)
        self.btn_4.clicked.connect(self.btn4)

        self.remind_time.timeout.connect(self.remind)
        self.record_time.timeout.connect(self.record)
        self.reshow_time.timeout.connect(self.reshow)
        self.request_time.timeout.connect(self.request)
        self.remind_time.start()

    def request(self):
        self.remind_time.start()
        self.request_time.stop()
        playsound(self.wav_in)

    def btn1(self):
        self.time = time.time()
        self.remind_time.stop()
        self.record_time.stop()
        self.request_time.stop()
        self.reshow_time.stop()
        self.re = 1
        self.hide()
        # os.system(self.wav_out)
        # play(self.out_sound)
        playsound(self.wav_out)
        # self.send_conn.send(self.wav_out)
        check_response(self, self.path)

    def btn2(self):
        self.time = time.time()
        self.remind_time.stop()
        self.record_time.stop()
        self.request_time.stop()
        self.reshow_time.stop()
        self.re = 2
        self.hide()
        # os.system(self.wav_out)
        # play(self.out_sound)
        playsound(self.wav_out)
        # self.send_conn.send(self.wav_out)
        check_response(self, self.path)

    def btn3(self):
        self.time = time.time()
        self.remind_time.stop()
        self.record_time.stop()
        self.request_time.stop()
        self.reshow_time.stop()
        self.re = 3
        self.hide()
        # os.system(self.wav_out)
        # play(self.out_sound)
        playsound(self.wav_out)
        # self.send_conn.send(self.wav_out)
        check_response(self, self.path)

    def btn4(self):
        self.time = time.time()
        self.remind_time.stop()
        self.record_time.stop()
        self.request_time.stop()
        self.reshow_time.stop()
        self.re = 4
        self.hide()
        # os.system(self.wav_out)
        # play(self.out_sound)
        playsound(self.wav_out)
        # self.send_conn.send(self.wav_out)
        check_response(self, self.path)

    def remind(self):
        self.remind_time.stop()
        self.record_time.start()
        self.hide()
        playsound(self.wav_in)
        self.show()

    def record(self):
        self.hide()
        self.time = time.time()
        playsound(self.wav_no_answer)
        self.record_time.stop()
        self.request_time.stop()
        self.reshow_time.start()
        raw_data = [(self.time, self.name, 0)]
        data = pd.DataFrame(raw_data, columns=self.df.columns)
        self.df = self.df.append(data)
        self.df.to_csv(f'{self.path}', index=False, encoding='utf-8-sig')
        self.show()

    def reshow(self):
        self.reshow_time.stop()
        self.remind_time.start()
        self.hide()
        playsound(self.wav_in)
        self.show()
