import time
import datetime
import pathlib
import serial
import pynmea2
import cantools
import can
import requests
import pandas as pd
import numpy as np
import configparser
import os
from check_status import check_driver, check_odometer


def request_traffic_info(lat, lon):
    try:
        r = requests.get(f"https://apis.openapi.sk.com/tmap/traffic?version=1&trafficType={str('POINT')}&centerLat={lat}&centerLon={lon}&zoomLevel=7&appKey=l7xxda3105b5da544f43aecda3971557249a")
        traffic_info = r.json()
    except:
        print("[WARNING] Traffic info request failed. WIFI or LTE could be the problem.")
        return None

    return traffic_info

def traffic_info_failed_data(traffic_cols, timestamp, fail_type):
    fail_data = [fail_type] * len(traffic_cols)
    fail_data[0] = timestamp
    # fail_data = [[timestamp] + fail_data]
    # print(fail_data)
    fail_data = pd.DataFrame([fail_data], columns=traffic_cols)

    return fail_data

def get_traffic_info_from_dict(traffic_info):
    try:
        traffic_feature = traffic_info['features'][0]
        traffic_properties = traffic_feature['properties']
        link_id = traffic_properties['id']
        link_name = traffic_properties['name']
        description = traffic_properties['description']
        if description == '':
            description = 'null'
        congestion = int(traffic_properties['congestion'])
        link_direction = int(traffic_properties['direction']) if traffic_properties['direction'] != 'null' else traffic_properties['direction']
        link_roadType = traffic_properties['roadType']
        startNodeName = traffic_properties['startNodeName']
        if startNodeName == '':
            startNodeName = 'null'
        endNodeName = traffic_properties['endNodeName']
        if endNodeName == '':
            endNodeName = 'null'
        link_length = float(traffic_properties['distance'])
        link_pass_time = float(traffic_properties['time'])
        link_speed = float(traffic_properties['speed'])
        traffic_updateTime = traffic_properties['updateTime']

        traffic_data = [link_id, link_name, description, congestion, traffic_updateTime, \
                        link_direction, link_roadType, startNodeName, endNodeName, link_length, link_pass_time, link_speed]
    except:
        traffic_data = None
    return traffic_data


def save_df(df, save_path, first):
    if save_path.parent.name == 'Traffic_info':
        if first:
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            first = False
        else:
            df.to_csv(save_path, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        if first:
            df.to_csv(save_path, index=False)
            first = False
        else:
            df.to_csv(save_path, mode='a', header=False, index=False)
    return first


def receive_GNSS(d_name, SAVE_PATH, config=None, print_status=True, receive_trf_info=False, stop_event=None):
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")
    # config = configparser.ConfigParser()
    # config.read('./config.ini')

    SAVE_PATH = pathlib.Path(SAVE_PATH)
    TRAFFIC_SAVE_PATH = SAVE_PATH / 'Traffic_info'
    TRAFFIC_SAVE_PATH.mkdir(exist_ok=True, parents=True)

    SAVE_PATH = SAVE_PATH / 'GNSS'
    SAVE_PATH.mkdir(exist_ok=True, parents=True)


    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.2)

    timestamp_col = ["Timestamp"]
    gnss_cols=["Latitude", "Longitude", "GPSMode", "SatelliteNum", "Altitude"]
    if receive_trf_info:
        traffic_cols = ['LinkID', 'LinkName', 'Description', 'Congestion', 'TrafficUpdateTime', \
                    'LinkDirection', 'LinkRoadType', 'StartNodeName', 'EndNodeName', 'LinkLength', 'LinkPassTime', 'LinkSpeed']
    yaw_col = ["Yaw"]
    imu_cols = ["Pitch", "Roll"]
    mag_cols = ["TrueNorth", "NorthDeclination"]
    # if receive_trf_info:
    #     total_cols = timestamp_col + gnss_cols + traffic_cols + yaw_col + imu_cols + mag_cols
    # else:
    total_cols = timestamp_col + gnss_cols + yaw_col + imu_cols + mag_cols
    gnss_cols = timestamp_col + gnss_cols
    if receive_trf_info:
        traffic_cols = timestamp_col + traffic_cols
    yaw_col = timestamp_col + yaw_col
    imu_cols = timestamp_col + imu_cols
    mag_cols = timestamp_col + mag_cols
    GNSS_TOTAL_NUM = 4
    total_df = pd.DataFrame(columns=total_cols)

    start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    SAVE_PATH = SAVE_PATH / str(start_time + ".csv")
    TRAFFIC_SAVE_PATH = TRAFFIC_SAVE_PATH / str(start_time + ".csv")


    today = datetime.datetime.today()
    request_period = float(config['GNSS']['trf_info_request_period'])
    req_time = time.time()
    gnss_cnt = 0
    first = True
    traffic_first = True
    full_alloc = False
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process starts collecting.")
    while True:
        try:
            try:
                recv = ser.readline().decode(encoding='utf-8')
                # print(recv)
                # print(type(recv))
                if recv.startswith('$'):
                    try:
                        record = pynmea2.parse(recv)
                        timestamp = record.timestamp
                        hour = int(timestamp.hour) + 9
                        if hour >= 24:
                            hour -= 24
                        minute = timestamp.minute
                        second = timestamp.second
                        microsecond = timestamp.microsecond
                        timestamp = datetime.datetime(year=today.year, month=today.month, day=today.day, hour=hour, minute=minute, second=second, microsecond=microsecond)
                        timestamp = timestamp.strftime("%Y_%m_%d_%H_%M_%S_%f")
                    except Exception as e:
                        # print("[EXCEPTION line 127]", e)
                        if stop_event is not None:
                            if stop_event.is_set():
                                break
                        continue

                    if recv.startswith('$GPGGA') or recv.startswith('$GNGGA'):
                        gnss_cnt += 1
                        lat = record.latitude
                        lon = record.longitude
                        gnss_data = [timestamp, lat, lon,
                                     record.gps_qual, record.num_sats, record.altitude]
                        gnss_df = pd.DataFrame([gnss_data], columns=gnss_cols)
                        gnss_timestamp = record.timestamp.strftime("%H_%M_%S_%f")

                        cur_time = time.time()
                        if receive_trf_info:
                            if (first or abs(cur_time - req_time) > request_period) and not full_alloc:
                                try:
                                    traffic_info = request_traffic_info(lat, lon)
                                    req_time = time.time()
                                except KeyboardInterrupt:
                                    break

                                if traffic_info is None:
                                    fail_type = 'req_failed'
                                    fail_data = traffic_info_failed_data(traffic_cols, timestamp, fail_type)
                                    traffic_first = save_df(fail_data, TRAFFIC_SAVE_PATH, traffic_first)

                                elif 'error' not in traffic_info.keys():
                                    traffic_data = get_traffic_info_from_dict(traffic_info)
                                    if traffic_data is not None:
                                        traffic_data = [[timestamp] + traffic_data]
                                        traffic_df = pd.DataFrame(traffic_data, columns=traffic_cols)
                                        traffic_first = save_df(traffic_df, TRAFFIC_SAVE_PATH, traffic_first)
                                    else:
                                        fail_type = 'req_failed'
                                        fail_data = traffic_info_failed_data(traffic_cols, timestamp, fail_type)
                                        traffic_first = save_df(fail_data, TRAFFIC_SAVE_PATH, traffic_first)

                                else:
                                    print("[INFO] Daily allocation is fully used. But no problem.\n")
                                    full_alloc = True
                            elif full_alloc:
                                # fail_data = ['full_alloc'] * len(traffic_cols)
                                # fail_data = [[timestamp] + fail_data]
                                # fail_data = pd.DataFrame(fail_data, columns=traffic_cols)
                                # gnss_df = pd.merge(gnss_df, fail_data, how='outer', on='Timestamp')
                                fail_type = 'full_alloc'
                                fail_data = traffic_info_failed_data(traffic_cols, timestamp, fail_type)
                                traffic_first = save_df(fail_data, TRAFFIC_SAVE_PATH, traffic_first)

                        if print_status:
                            print(f"[INFO] Time[{timestamp[11:19]}] LAT[{record.latitude:.6f}] LON[{record.longitude:.6f}] ALT[{record.altitude:.2f}]", end='\r')

                    elif recv.startswith('$GPRMC') or recv.startswith('$GNRMC'):
                        gnss_cnt += 1
                        true_north = record.true_course
                        mag_timestamp = record.timestamp.strftime("%H_%M_%S_%f")
                        north_declination = record.mag_variation
                        mag_data = [[timestamp, true_north, north_declination]]
                        # print("here ", mag_data)
                        mag_df = pd.DataFrame(mag_data, columns=mag_cols)
                        pass
                    # elif recv.startswith('$GPGSV') or recv.startswith('$BDGSV') or recv.startswith('$GBGSV') or recv.startswith('$GLGSV'):
                    #     if record.msg_num =='1':
                    #         print('Number of Satellites in View:', record.num_sv_in_view)
                    # elif recv.startswith('$GPGSA') or recv.startswith('$BDGSA') or recv.startswith('$GNGSA'):
                    #         print('Fixed Satellites No.: ', record.sv_id01, record.sv_id02, record.sv_id03, record.sv_id04,record.sv_id05, record.sv_id06,record.sv_id07, record.sv_id08,record.sv_id09, record.sv_id10,record.sv_id11, record.sv_id12)

                    elif recv.startswith('$PASHR'):
                        gnss_cnt += 1
                        imu_timestamp = record.timestamp.strftime("%H_%M_%S_%f")
                        pitch = record.pitch
                        roll = record.roll
                        imu_data = [[timestamp, pitch, roll]]
                        imu_df = pd.DataFrame(imu_data, columns=imu_cols)

                    elif recv.startswith('$PTNL'):
                        gnss_cnt += 1
                        yaw_timestamp = record.timestamp.strftime("%H_%M_%S_%f")
                        yaw = record.yaw_angle
                        yaw_data = [[timestamp, yaw]]
                        yaw_df = pd.DataFrame(yaw_data, columns=yaw_col)
                        pass
                else:
                    # print("recv empty")
                    pass
                # print(gnss_cnt)
                # print(gnss_timestamp, mag_timestamp, imu_timestamp, yaw_timestamp)
                if gnss_cnt >= GNSS_TOTAL_NUM and gnss_timestamp == mag_timestamp and \
                    gnss_timestamp == imu_timestamp and gnss_timestamp == yaw_timestamp:
                    gnss_cnt = 0
                    tmp_df = pd.merge(gnss_df, yaw_df, how='outer', on='Timestamp')
                    tmp_df = pd.merge(tmp_df, imu_df, how='outer', on='Timestamp')
                    tmp_df = pd.merge(tmp_df, mag_df, how='outer', on='Timestamp')
                    total_df = total_df[0:0]
                    total_df = total_df.append(tmp_df)
                    first = save_df(total_df, SAVE_PATH, first)

            except Exception as e:
                # print('lat lon empty')
                # print("[EXCEPTION line 236]", e)
                gnss_cnt = 0
                if stop_event is not None:
                    if stop_event.is_set():
                        break
                continue

            if stop_event is not None:
                if stop_event.is_set():
                    break

        except KeyboardInterrupt:
            break

    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")

def main():
    from config import config

    print("+++ GNSS PROCESS +++")
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.2)


    # config = configparser.ConfigParser()
    # config.read('./config.ini')


    SAVE_BASE_PATH = pathlib.Path(config['SAVE_PATH'])

    DRIVER_LIST = config['DRIVER_LIST']
    DRIVER_NAME = check_driver(DRIVER_LIST)
    SAVE_PATH = SAVE_BASE_PATH / DRIVER_NAME

    C_CAN_path = SAVE_BASE_PATH / "dbc" / "C_CAN.dbc"
    C_db = cantools.database.load_file(C_CAN_path)
    can_bus = can.interface.Bus('can0', bustype='socketcan')
    START_ODO = check_odometer(C_db, can_bus)

    SAVE_PATH = SAVE_PATH / str(START_ODO) #/ "GNSS"
    # SAVE_PATH.mkdir(exist_ok=True, parents=True)

    receive_GNSS("GNSS", SAVE_PATH, config)
    # timestamp_col = ["Timestamp"]
    # gnss_cols=["Latitude", "Longitude", "GPSMode", "SatelliteNum", "Altitude"]
    # traffic_cols = ['LinkID', 'LinkName', 'Description', 'Congestion', 'TrafficUpdateTime', \
    #             'LinkDirection', 'LinkRoadType', 'StartNodeName', 'EndNodeName', 'LinkLength', 'LinkPassTime', 'LinkSpeed']
    # yaw_col = ["Yaw"]
    # imu_cols = ["Pitch", "Roll"]
    # mag_cols = ["TrueNorth", "NorthDeclination"]
    # total_cols = timestamp_col + gnss_cols + traffic_cols + yaw_col + imu_cols + mag_cols
    # gnss_cols = timestamp_col + gnss_cols
    # traffic_cols = timestamp_col + traffic_cols
    # yaw_col = timestamp_col + yaw_col
    # imu_cols = timestamp_col + imu_cols
    # mag_cols = timestamp_col + mag_cols
    # GNSS_TOTAL_NUM = 4
    # total_df = pd.DataFrame(columns=total_cols)

    # start_time = time.strftime("%Y_%m_%d_%H_%M", time.localtime(time.time()))
    # SAVE_PATH = SAVE_PATH / str(start_time + ".csv")


    # today = datetime.datetime.today()
    # request_period = float(config['GNSS']['trf_info_request_period'])
    # req_time = time.time()
    # gnss_cnt = 0
    # first = True
    # full_alloc = True

    # while True:
    #     try:
    #         try:
    #             recv = ser.readline().decode()
    #             if recv.startswith('$'):
    #                 record = pynmea2.parse(recv)
    #                 timestamp = record.timestamp
    #                 try:
    #                     hour = int(timestamp.hour) + 9
    #                     minute = timestamp.minute
    #                     second = timestamp.second
    #                     microsecond = timestamp.microsecond
    #                     timestamp = datetime.datetime(year=today.year, month=today.month, day=today.day, hour=hour, minute=minute, second=second, microsecond=microsecond)
    #                     timestamp = timestamp.strftime("%Y_%m_%d_%H_%M_%S_%f")
    #                 except:
    #                     continue

    #                 if recv.startswith('$GPGGA') or recv.startswith('$GNGGA'):
    #                     gnss_cnt += 1
    #                     lat = record.latitude
    #                     lon = record.longitude
    #                     gnss_data = [timestamp, lat, lon,
    #                                  record.gps_qual, record.num_sats, record.altitude]
    #                     gnss_df = pd.DataFrame([gnss_data], columns=gnss_cols)
    #                     gnss_timestamp = record.timestamp.strftime("%H_%M_%S_%f")

    #                     cur_time = time.time()
    #                     if (first or abs(cur_time - req_time) > request_period) and not full_alloc:
    #                         try:
    #                             traffic_info = request_traffic_info(lat, lon)
    #                             req_time = time.time()
    #                         except KeyboardInterrupt:
    #                             break

    #                         if 'error' not in traffic_info.keys():
    #                             traffic_data = get_traffic_info_from_dict(traffic_info)
    #                             traffic_data = [[timestamp] + traffic_data]
    #                             traffic_df = pd.DataFrame(traffic_data, columns=traffic_cols)
    #                             gnss_df = pd.merge(gnss_df, traffic_df, how='outer', on='Timestamp')
    #                         else:
    #                             print("[INFO] Daily allocation is fully used. But no problem.")
    #                             full_alloc = True
    #                     print(f"[INFO] Time[{timestamp[11:19]}] LAT[{record.latitude:.6f}] LON[{record.longitude:.6f}] ALT[{record.altitude:.2f}]", end='\r')

    #                 elif recv.startswith('$GPRMC') or recv.startswith('$GNRMC'):
    #                     gnss_cnt += 1
    #                     mag_timestamp = record.timestamp.strftime("%H_%M_%S_%f")
    #                     true_north = record.true_course
    #                     north_declination = record.mag_variation
    #                     mag_data = [[timestamp, true_north, north_declination]]
    #                     mag_df = pd.DataFrame(mag_data, columns=mag_cols)
    #                     pass
    #                 # elif recv.startswith('$GPGSV') or recv.startswith('$BDGSV') or recv.startswith('$GBGSV') or recv.startswith('$GLGSV'):
    #                 #     if record.msg_num =='1':
    #                 #         print('Number of Satellites in View:', record.num_sv_in_view)
    #                 # elif recv.startswith('$GPGSA') or recv.startswith('$BDGSA') or recv.startswith('$GNGSA'):
    #                 #         print('Fixed Satellites No.: ', record.sv_id01, record.sv_id02, record.sv_id03, record.sv_id04,record.sv_id05, record.sv_id06,record.sv_id07, record.sv_id08,record.sv_id09, record.sv_id10,record.sv_id11, record.sv_id12)

    #                 elif recv.startswith('$PASHR'):
    #                     gnss_cnt += 1
    #                     imu_timestamp = record.timestamp.strftime("%H_%M_%S_%f")
    #                     pitch = record.pitch
    #                     roll = record.roll
    #                     imu_data = [[timestamp, pitch, roll]]
    #                     imu_df = pd.DataFrame(imu_data, columns=imu_cols)

    #                 elif recv.startswith('$PTNL'):
    #                     gnss_cnt += 1
    #                     yaw_timestamp = record.timestamp.strftime("%H_%M_%S_%f")
    #                     yaw = record.yaw_angle
    #                     yaw_data = [[timestamp, yaw]]
    #                     yaw_df = pd.DataFrame(yaw_data, columns=yaw_col)
    #                     pass

    #             if gnss_cnt >= GNSS_TOTAL_NUM and gnss_timestamp == mag_timestamp and \
    #                 gnss_timestamp == imu_timestamp and gnss_timestamp == yaw_timestamp:
    #                 gnss_cnt = 0
    #                 tmp_df = pd.merge(gnss_df, yaw_df, how='outer', on='Timestamp')
    #                 tmp_df = pd.merge(tmp_df, imu_df, how='outer', on='Timestamp')
    #                 tmp_df = pd.merge(tmp_df, mag_df, how='outer', on='Timestamp')
    #                 total_df = total_df[0:0]
    #                 total_df = total_df.append(tmp_df)
    #                 if first:
    #                     total_df.to_csv(SAVE_PATH, index=False)
    #                     first = False
    #                 else:
    #                     total_df.to_csv(SAVE_PATH, mode='a', header=False, index=False)

    #         except pynmea2.nmea.ParseError:
    #             # print('NMEA wrong！')
    #             gnss_cnt = 0

    #     except KeyboardInterrupt:
    #         break

    print("\n[INFO]GNSS finished.")


if __name__ == '__main__':
    main()
