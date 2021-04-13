import cantools
import can
from pprint import pprint
import time

db = cantools.database.load_file('/media/imlab/62C1-3A4A/AE_PE_C_C_KOOKMIN_2/AE_PE_C_C_KOOKMIN_2.dbc')
print(db.messages)
can_bus = can.interface.Bus('can0', bustype='socketcan')
# message = can_bus.recv()
# print(message.data)
# for _ in range(10):
esp = 0
sas = 0
whl = 0
esp_frame_id = 0.0
sas_frame_id = 0.0
whl_frame_id = 0.0
for message in db.messages:
    if message.name == 'ESP12':
        esp_frame_id = message.frame_id
    elif message.name == 'SAS11':
        sas_frame_id = message.frame_id
    elif message.name == 'WHL_SPD11':
        whl_frame_id = message.frame_id

while(True):
    try:
        message = can_bus.recv()
        if message.arbitration_id == esp_frame_id:
            esp = db.decode_message(mesage.arbitration_id, message.data)['CYL_PRES']

        elif message.arbitration_id == sas_frame_id:
            sas = db.decode_message(message.arbitration_id, message.data)['SAS_Angle']
        
        elif message.arbitration_id == whl_frame_id:
            whl = db.decode_message(message.arbitration_id, message.data)['WHL_SPD_FL']

        print("ESP : {:08.5f},  SAS : {:08.5f},  WHL {:08.5f}".format(esp, sas, whl))
        # time.sleep(0.001)
        # break
    except:
        pass