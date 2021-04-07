import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ipaddr = socket.gethostbyname(socket.gethostname())
client_socket.bind((ipaddr, 63332))
client_socket.connect(('203.246.114.193', 22222))
data1 = 123
data2 = 234
send_data = "{} {}".format(data1, data2)
while True:
    client_socket.send(send_data.encode())