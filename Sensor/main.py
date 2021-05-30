## Test file for 'receive_sensor' thread
import threading
from receive_sensor import receive_sensor

def sensor_main():
    print("Main thread started.")

    ### Sensor setting ###

    ### Thread setting ###
    stop_threads = False
    workers = []
    data_names = ['sensor']
    thread_functions = [receive_sensor]
    func_args = {
                 'sensor': (),
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
    sensor_main()