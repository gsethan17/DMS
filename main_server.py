import socket
from _thread import *
from server_recv import *


serversocket=socket.socket()

HOST = socket.gethostname()
ip_addr = socket.gethostbyname(HOST)
port = 22222
ThreadCount = 0

try:
    serversocket.bind((ip_addr, port))
except socket.error as e:
    print(str(e))
print("Waiting for connection")
serversocket.listen(5)


while True:
    client,address=serversocket.accept()
    print("Connected to : "+address[0]+" "+str(address[1]))
    print("Client", client)
    print(address[1])
    client_port = address[1]

    if (client_port==63333):
        print("Image Data")
        start_new_thread(get_video_stream,(client,))
    else:
        print("Serial Data")
        start_new_thread(get_CAN_signal,(client,))

    ThreadCount+=1
    print("ThreadNumber="+str(ThreadCount))
serversocket.close()









