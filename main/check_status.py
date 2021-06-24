import cantools
import can


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
            CGW_dict = P_db.decode_message(can_msg.arbitration_id, can_msg.data)
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
    check_name = 'n'
    check_id = 'n'

    DRIVER_NAME = 'n'
    DRIVER_ID = -1

    while check_name != 'y' :
        print()
        print("#" * 10, "DRIVER ID", "#" * 10)
        for i, name in enumerate(DRIVER_LIST):
            if i != len(DRIVER_LIST) - 1:
                print(f"{DRIVER_LIST[i]}: {DRIVER_LIST.index(DRIVER_LIST[i])}, ", end=' ')
            else:
                print(f"{DRIVER_LIST[i]}: {DRIVER_LIST.index(DRIVER_LIST[i])}")
        print("#" * 31)
        print()

        check_name = input("[REQUEST] Is there your name in above list? [y/n] ")
        if check_name == 'y':
            while check_id != 'y':
                DRIVER_ID = int(input("[REQUEST] Enter your DRIVER ID : "))
                check_id = input(f"[REQUEST] Is your name {DRIVER_LIST[DRIVER_ID]}? [y/n] ")
            DRIVER_NAME = DRIVER_LIST[DRIVER_ID]
        else:
            DRIVER_NAME = input("[REQUEST] Enter your name: ")
            DRIVER_LIST.append(str(DRIVER_NAME))
    
    return DRIVER_NAME

def check_odd():
    check_odd = 'n'
    while check_odd != 'y' :
        try:
            ODD = input("[REQUEST] Enter current odd meter : ")
            check_odd = input("[REQUEST] Is current odd meter {} km? [y/n] ".format(int(ODD)))
        except:
            print("Invalid input. Try again.")
    return ODD

def check_intention():
    start_flag = 'n'
    while start_flag != 'y' :
        start_flag = input("[REQUEST] Do you want to start collecting and storing data? [y/n] ")