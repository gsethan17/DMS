import cantools
import can
import math


def check_driving_cycle(P_db, can_bus):
    print("[INFO] Check driving cycle...")

    for msg in P_db.messages:
        if msg.name == 'CGW1':
            CGW_CAN = msg
    cycle_cnt = 0
    start_flag = False
    
    while True:
        can_msg = can_bus.recv()
        if can_msg.arbitration_id == CGW_CAN.frame_id:
            CGW_dict =P_db.decode_message(can_msg.arbitration_id, can_msg.data)
            if CGW_dict['CF_Gway_IGNSw'] == 'IGN':
                cycle_cnt += 1
                start_flag = True
            elif not start_flag:
                print("[REQUEST] Starting the car is needed.")
                start_flag = True

        if cycle_cnt >= 10:
            print("[INFO] Done.")
            break

def check_velocity(P_db, can_bus):
    print("[INFO] Check velocity...")
    for msg in P_db.messages:
        if msg.name == 'WHL_SPD11':
            WHL_CAN = msg
    whl_spd_key = ['WHL_SPD_FL', 'WHL_SPD_FR', 'WHL_SPD_RL', 'WHL_SPD_RR']
    spd_cnt = 0
    spd_flag = False
    while True:
        can_msg = can_bus.recv()
        if can_msg.arbitration_id == WHL_CAN.frame_id:
            WHL_dict = P_db.decode_message(can_msg.arbitration_id, can_msg.data)
            whl_spd = [WHL_dict[key] for key in whl_spd_key]
            mean_spd = sum(whl_spd) / len(whl_spd)

            if mean_spd <= 4.: ## 4km/h
                spd_cnt += 1
                spd_flag = True
            elif not spd_flag:
                print("[REQUEST] Park the car in a safe place.")
                spd_flag = True

        if spd_cnt >= 10:
            print("[INFO] done.")
            break

def check_driver(DRIVER_LIST):    
    check_name = ''
    check_id = ''
    check_input_name = ''
    DRIVER_NAME = ''
    DRIVER_ID = -1

    while True :
        print()
        print("#" * 10, "DRIVER ID", "#" * 10)
        for i, name in enumerate(DRIVER_LIST):
            if i != len(DRIVER_LIST) - 1:
                print(f"{DRIVER_LIST.index(DRIVER_LIST[i])}: {DRIVER_LIST[i]}, ", end=' ')
            else:
                print(f"{DRIVER_LIST.index(DRIVER_LIST[i])}: {DRIVER_LIST[i]}")
        print("#" * 31)
        print()

        while True :
            check_name = input("[REQUEST] Is there your name in above list? [y/n] ")
            if check_name == 'y':
                while True:
                    DRIVER_ID = input("[REQUEST] Enter your DRIVER ID (Back to the list => Press 'b') : ")
                    if DRIVER_ID == 'b':
                        break
                    elif DRIVER_ID != 'b' and DRIVER_ID.isnumeric() and int(DRIVER_ID) < len(DRIVER_LIST):
                        DRIVER_ID = int(DRIVER_ID)
                    else:
                        print("[INFO] Invalid input. Try again.")
                        continue
                    while True:
                        check_id = input(f"[REQUEST] Is your name {DRIVER_LIST[DRIVER_ID]}? (Back to the list => Press 'b') [y/n] ")
                        if check_id == 'y' or check_id == 'n' or check_id == 'b':
                            break
                        else:
                            print("[INFO] Invalid input. Try again.")
                    if check_id == 'y' or check_id == 'b':
                        break
                    if check_id == 'n':
                        continue
                if DRIVER_ID == 'b' or check_id == 'b':
                    break
                else:
                    DRIVER_NAME = DRIVER_LIST[DRIVER_ID]
                    check_input_name == ''
                    break

            elif check_name == 'n':
                while True :
                    DRIVER_NAME = input("[REQUEST] Enter your name (Back to the list => Press 'b') : ")
                    if DRIVER_NAME == 'b':
                        break
                    else:
                        while True:
                            check_input_name = input(f"[REQUEST] Is your name {DRIVER_NAME}? (Back to the list => Press 'b') [y/n] ")
                            if check_input_name == 'y':
                                DRIVER_LIST.append(str(DRIVER_NAME))
                                break
                            elif check_input_name == 'n' or check_input_name == 'b':
                                break
                            else:
                                print("[INFO] Invalid input. Try again.")
                        if check_input_name == 'y' or check_input_name == 'b':
                            break
                        elif check_input_name == 'n':
                            continue
                if DRIVER_NAME == 'b' or check_input_name == 'y' or check_input_name == 'b':
                    break
            else:
                print("[INFO] Invalid input. Try again.")
        if DRIVER_ID == 'b' or DRIVER_NAME == 'b' or check_id == 'b':
            DRIVER_ID == ''
            DRIVER_NAME == ''
            check_id == ''
            continue
        if check_input_name == 'y' or check_input_name == 'b':
            check_input_name = ''
            continue
        if DRIVER_NAME in DRIVER_LIST:
            # print(DRIVER_LIST)
            break


    return DRIVER_NAME

def check_odometer(C_db, can_bus):
    print("[INFO] Check odometer...")

    ODOMETER = 0
    for msg in C_db.messages:
        if msg.name == 'CLU12':
            CLU_CAN = msg
    cycle_cnt = 0
    start_flag = False
    
    while True:
        can_msg = can_bus.recv()
        if can_msg.arbitration_id == CLU_CAN.frame_id:
            CLU_dict = C_db.decode_message(can_msg.arbitration_id, can_msg.data)
            ODOMETER = str(math.floor(CLU_dict['CF_Clu_Odometer']))
            print(f"[INFO] Currunt odometer : {ODOMETER} km")
            break
    return ODOMETER
     

def check_intention():
    start_flag = 'n'
    while start_flag != 'y' :
        start_flag = input("[REQUEST] Do you want to start collecting and storing data? [y/n] ")
