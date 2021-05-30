## Test file for 'receive_CAN' thread
import threading
import cantools
import can
import time
import sys
from receive_CAN import receive_CAN

TOTAL_THREADS_NUM = 1
thread_count = 0

def CAN_main():
    print("Main thread started.")
    
    ### CAN setting ###
    db = cantools.database.load_file('/media/imlab/62C1-3A4A/AE_PE_C_C_KOOKMIN_2/AE_PE_C_C_KOOKMIN_2.dbc')
    can_bus = can.interface.Bus('can0', bustype='socketcan')

    ### Thread setting ###
    stop_threads = False
    workers = []
    data_names = ['CAN']
    thread_functions = [receive_CAN]
    func_args = {'CAN': (db, can_bus),
                 }
    
    ### Thread generation ###
    print("Press 'Enter' if you want to terminate every processes.")
    for d_name, th_func in zip(data_names, thread_functions):
        worker = threading.Thread(target=th_func.th_func, args=(d_name, *func_args[d_name], lambda: stop_threads))
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
    CAN_main()