## Test file for 'receive_audio' thread
import threading
import pyaudio
# from receive_audio import receive_audio

SINGLE_THREAD = 0

def audio_main():
    from receive_audio import receive_audio
    
    print("Main thread started.")
    SINGLE_THREAD = 1

    ### Audio setting ###
    FORMAT = pyaudio.paInt16
    RATE = 44100
    CHANNELS = 1
    CHUNK = 1024

    ### Thread setting ###
    stop_threads = False
    workers = []
    data_names = ['audio']
    thread_functions = [receive_audio]
    func_args = {
                 'audio': (FORMAT, RATE, CHANNELS, CHUNK),
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
    audio_main()