import struct
import pickle
import cv2

def get_video_stream(conn):
    data = b""
    payload_size = struct.calcsize(">L")
    # print("payload_size: {}".format(payload_size))
    while True:
        while len(data) < payload_size:
            # print("Recv: {}".format(len(data)))
            data += conn.recv(4096)

        # print("Done Recv: {}".format(len(data)))
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        # print("msg_size: {}".format(msg_size))
        while len(data) < msg_size:
            data += conn.recv(4096)
        frame_data = data[:msg_size]
        # print(frame_data)
        data = data[msg_size:]

        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        cv2.imshow('ImageWindow', frame)
        cv2.waitKey(1)


def get_CAN_signal(conn):
    while True:
        data = conn.recv(7)
        received = str(data, encoding='utf-8')
        # print(received)
