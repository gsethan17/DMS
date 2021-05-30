from ../main import TOTAL_THREADS_NUM, thread_count
import threading
import time
import pandas as pd

import cantools
import can

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

def receive_CAN(d_name, db, can_bus, stop):
    print(f"'{d_name}' thread started.")

    df = pd.DataFrame(columns=['timestamp'])
    can_monitoring = dict()

    sync_thread()

    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    while(True):
        try:
            can_msg = can_bus.recv()
            for db_msg in db.messages:
                if can_msg.arbitration_id == db_msg.frame_id:
                    can_dict = db.decode_message(can_msg.arbitration_id, can_msg.data)
                    can_dict['timestamp'] = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
                    df = df.append(can_dict, ignore_index=True)

                    ## For monitoring
                    if db_msg.name == 'ESP12':
                        can_monitoring['ESP12'] = can_dict['CYL_PRES']
                    elif db_msg.name == 'SAS11':
                        can_monitoring['SAS11'] = can_dict['SAS_Angle']
                    elif db_msg.name == 'WHL_SPD11':
                        can_monitoring['WHL_SPD11'] = can_dict['WHL_SPD_FL']
            print("ESP: {:08.5f},  SAS: {:08.5f},  WHL: {:08.5f}".format(can_monitoring['ESP12'], can_monitoring['SAS11'], can_monitoring['WHL_SPD11']), end='\r')

            if stop():
                break
            
        except:
            if stop():
                break

    df.to_csv(f"../DMS_dataset/can/{start_time}.csv")
    print(f"'{d_name}' thread terminated.")