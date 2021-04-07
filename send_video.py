import cv2
import socket
import struct
import time
import pickle


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(client_socket)
ipaddr = socket.gethostbyname(socket.gethostname())
client_socket.bind((ipaddr, 63333))
client_socket.connect(('203.246.114.193', 22222))
connection = client_socket.makefile('wb')

cam = cv2.VideoCapture(0)

# cam.set(3, 320*2);
# cam.set(4, 240*2);
# print("Camera Open")

img_counter = 0

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

while True:
    ret, frame = cam.read()


    if ret:
        result, frame = cv2.imencode('.jpg', frame, encode_param)
        print(type(frame))
        print(frame.shape)
        print(frame.shape[0])
        data = pickle.dumps(frame, 0)
        size = len(data)
        # print("{}: {}".format(img_counter, size))
        client_socket.sendall(struct.pack(">L", size) + data)
        time.sleep(0.1)
        img_counter += 1

        key = cv2.waitKey(1) & 0xff
        if key == ord('q'):
            client_socket.close()

cam.release()