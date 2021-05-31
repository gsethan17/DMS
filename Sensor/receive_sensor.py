from main_sensor import SINGLE_THREAD
from ..main import TOTAL_THREADS_NUM, thread_count
import threading

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

def receive_sensor():
    global SINGLE_THREAD

    if SINGLE_THREAD == 0:
        sync_thread()
        
    pass