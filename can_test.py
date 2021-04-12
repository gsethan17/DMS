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
st = time.time()
while(True):
    try:
        message = can_bus.recv()
        # print(message.data)
        if message.arbitration_id == 0x220:
            esp = db.decode_message('ESP12', message.data)['CYL_PRES']

        elif message.arbitration_id == 0x2b0:
            sas = db.decode_message('SAS11', message.data)['SAS_Angle']
        
        elif message.arbitration_id == 0x386:
            whl = db.decode_message('WHL_SPD11', message.data)['WHL_SPD_FL']

        print("ESP : {:08.5f},  SAS : {:08.5f},  WHL {:08.5f}".format(esp, sas, whl))
        # en = time.time()
        # print(en - st)
        # st = time.time()
        # print(db.decode_message('ESP12', message.data))
        # print(db.decode_message('WHL_SPD11', message.data))
        # print(esp.decode(message.data)['CYL_PRES'])
        # time.sleep(0.001)
        # break
    except:
        pass
    # time.sleep(1)
    # message = can_bus.recv()

# import canlib
# from canlib import kvadblib
# from canlib import canlib
# import can

# db = kvadblib.Dbc(filename="/media/imlab/62C1-3A4A/AE_PE_C_C_KOOKMIN_2/AE_PE_C_C_KOOKMIN_2.dbc")
# can_bus = can.interfaces.kvaser.canlib.KvaserBus(0)