import cantools
import can
import math

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