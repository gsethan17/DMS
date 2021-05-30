## Test file for 'receive_video' thread
import threading
from receive_video import receive_video

TOTAL_THREADS_NUM = 1
thread_count = 0

def video_main():
    print("Main thread started.")

    ### Thread setting ###
    stop_threads = False
    workers = []
    data_names = ['video']
    thread_functions = [receive_video]
    func_args = {
                 'video': (),
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
    video_main()