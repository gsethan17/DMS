from main import TOTAL_THREADS_NUM, thread_count
import threading
import time
import datetime as dt
import os

import cv2

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