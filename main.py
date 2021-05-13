import threading
import cantools
import can
import pyaudio
import time
from receive_data import *

## These variables are used in receive_data.py to sync threads
TOTAL_THREAD_NUM = 3 ## Add +1 whenever sensor added.
thread_count = 0

def main():
    print("Main thread started.")
    ### CAN setting ###
    db = cantools.database.load_file('/media/imlab/62C1-3A4A/AE_PE_C_C_KOOKMIN_2/AE_PE_C_C_KOOKMIN_2.dbc')
    can_bus = can.interface.Bus('can0', bustype='socketcan')

    ### Audio setting ###
    FORMAT = pyaudio.paInt16
    RATE = 44100
    CHANNELS = 1
    CHUNK = 1024
    duration = 5

    ### Thread setting ###
    stop_threads = False
    workers = []
    data_names = ['CAN', 'video', 'audio']
    thread_functions = [receive_CAN, receive_video, receive_audio]
    func_args = {'CAN': (db, can_bus),
                 'video': (),
                 'audio': (FORMAT, RATE, CHANNELS, CHUNK, duration),
                 }
    print("Press 'Enter' if you want to terminate every processes.")
    for d_name, th_func in zip(data_names, thread_functions):
        worker = threading.Thread(target=th_func, args=(d_name, *func_args[d_name], lambda: stop_threads))
        workers.append(worker)
        worker.start()
    
    
    terminate_signal = input()
    while terminate_signal != '':
        print("Wrong input! Press 'Enter'")
        terminate_signal = input()
    stop_threads = True

    for worker in workers:
        worker.join()
    print("Main thread finished.")

    
if __name__ == "__main__":
    main()