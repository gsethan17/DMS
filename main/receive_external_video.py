import multiprocessing
import cv2
import os
import time

def receive_usb_cam(d_name, save_flag, DATASET_PATH, fc_view, flag_show, stop_event):
    PATH = DATASET_PATH + '/video/external/'

    if save_flag:
        if not os.path.isdir(PATH):
            os.makedirs(PATH)
        if fc_view:
            PATH_FC = PATH + 'FrontCenter/'
            if not os.path.isdir(PATH_FC):
                os.makedirs(PATH_FC)

    if fc_view:
        cap = cv2.VideoCapture(1)
        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = int(1000/fps)

    try:
        while cap.isOpened():
            cur_time = time.time()
            flag, img = cap.read()

            if flag & save_flag:
                print(PATH_FC + f"{cur_time}.png")
                cv2.imwrite(PATH_FC + f"{cur_time}.png", img)
            
            if flag_show:
                cv2.imshow('frame', img)
                if 0xFF == ord('q'):
                    break

            if stop_event is not None:
                if stop_event.is_set():
                    break
            
            cv2.waitKey(delay)

    except Exception as e:
        print(e)

    finally:
        if fc_view:
            # close
            cap.release()
            print('close...')

    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")

if __name__ == '__main__':
    d_name = 'out_video'
    save_flag = True
    DATASET_PATH = os.getcwd()
    fc_view = True
    flag_show = True

    receive_usb_cam(d_name, save_flag, DATASET_PATH, fc_view, flag_show, None)