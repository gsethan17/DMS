import socket
from _thread import *
from server_recv import *


serversocket=socket.socket()

HOST = socket.gethostname()
print("==========Drive Monitoring System==========")
print("HOST NAME --> ", HOST)
#ip_addr = socket.gethostbyname(HOST)
ip_addr = "113.198.211.159"
print("IP ADDR --> ", ip_addr)
port = 22222
print("===========================================")
ThreadCount = 0

try:
    serversocket.bind(("113.198.211.159", port))
except socket.error as e:
    print(str(e))
print("[INFO] Waiting for connection...")
serversocket.listen(5)


while True:
    client,address=serversocket.accept()
    print("==============================")
    print("[INFO] Connected to : "+address[0]+" "+str(address[1]))
   # print("Client", client)
    print(address[1])
    client_port = address[1]

    if (client_port==63333):
        print("[INFO] Image Data")
        start_new_thread(get_video_stream,(client,))
    
    elif (client_port==63331) :
        print("[INFO] Audio Data")
        start_new_thread(get_audio_stream, (client,))
    
    elif (client_port==63332):
        print("[INFO] CAN Data")
        start_new_thread(get_CAN_signal,(client,))
    else:
        print("[INFO] MISC Data")
        start_new_thread(get_MISC_signal,(client,))

    ThreadCount+=1
    print("[INFO] ThreadNumber ==>"+str(ThreadCount))
    print("===============================")


serversocket.close()









