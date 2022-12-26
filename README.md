# DMS
Driver Monitoring System

## Updates Histopy
* v0.0 : Initial version        [Released Data : 2021-07-01]
* v0.1 : CAN signal update      [Released Data : 2021-08-20]
* v0.2 : HMI & odometer update  [Release Data : 2021-09-13]
* v0.2.1 : Audio synchronization test branch [Release Data : 2021-09-30]
* v1.0.0 : Real-time traffic info & GNSS (RTK) [Release Data : 2022-10-07]
* v1.1.0 : Front-view exteral video [Release Data : TBD]

## Build environments
* sudo apt install ffmpeg

## Data application lists
* External Video
  - [ ] RGB images of front view towards the vehicle heading (TBD)
* Internal Video
  - [x] RGB images of front view towards the driver (.avi)
  - [x] IR images of front view towards the driver (.avi)
  - [ ] Depth images of front view towards the driver
  - [x] RGB images of side view towards the driver (.avi)
  - [x] IR images of side view towards the driver (.avi)
  - [ ] Depth images of side view towards the driver
* CAN data 
  - [x] A_Depth : Accel Pedal State (%)
  - [x] B_Depth : Brake Pedal state (%)
  - [x] B_PRES  : Brake Presure (TBD)
  - [x] B_FLAG  : Brake Operation Flag
  - [x] S_Angle : Steering Wheel Angle (<sup>o</sup>)
  - [x] HL_High : Headlamp High-Beam Operation
  - [x] HL_Low  : Headlamp High-Beam Operation
  - [x] DriveMode : Drive Mode
  - [x] HevMode     : Hybrid Mode
  - [x] E_Status    : Enine Status
  - [x] E_Col_Temp  : Engine Coolant Temperature (<sup>o</sup>C)
  - [x] E_Speed     : Engine RPM (rpm)
  - [x] F_Consump   : Fuel Consumption (TBD)
  - [x] Eco_Level   : TBD
  - [x] F_Economy   : Fuel Economy (km/L)
  - [x] BA_SoC      : Battery SoC
  - [x] LAT_ACCEL   : Lateral Acceleration (TBD)
  - [x] LONG_ACCEL  : Longitudinal Acceleration (TBD)
  - [x] YAW_RATE    : YAW_RATE (TBD)
  - [x] WHL_SPD_FR : Vehicle speed on each wheels (Front Right) (kph)
  - [x] WHL_SPD_FL : Vehicle speed on each wheels (Front Left) (kph)
  - [x] WHL_SPD_RR : Vehicle speed on each wheels (Rear Right) (kph)
  - [x] WHL_SPD_RL : Vehicle speed on each wheels (Rear Left) (kph)
  - [x] V_Spped     : Vehicle speed (kph)
  - [x] G_Status    : Gear Status
  - [x] Inhibit_P   : Parking Gear Status
  - [x] Inhibit_R   : Reverse Gear Status
  - [x] Inhibit_N   : Neutral Gear Status
  - [x] Inhibit_D   : Drive Gear Status
  - [x] Out_Temp    : Ambient Temperature (<sup>o</sup>C)
* Real-time traffic information
  - [x] LinkID            : TBD
  - [x] LinkName          : TBD
  - [x] Description       : TBD
  - [x] Congestion        : TBD
  - [x] TrafficUpdateTime : TBD
  - [x] LinkDirection     : TBD
  - [x] LinkRoadType      : TBD
  - [x] StartNodeName     : TBD
  - [x] EndNodeName       : TBD
  - [x] LinkLength        : TBD
  - [x] LinkPassTime      : TBD
  - [x] LinkSpeed         : TBD
* GNSS(Global Navigation Satellite System) w/RTK(Real Time Kinematic)
  - [x] Latitude          : TBD
  - [x] Longitude         : TBD
  - [x] GPSMode           : TBD
  - [x] SatelliteNum      : TBD
  - [x] Altitude          : TBD
  - [x] Yaw               : TBD
  - [x] Pitch             : TBD
  - [x] Roll              : TBD
  - [x] TrueNorth         : TBD
  - [x] NorthDeclination  : TBD


▼▼▼▼▼▼▼▼ Deactivate data ▼▼▼▼▼▼▼▼ (please refer to [config file](./main/config.py))
* Driver affective state
  - [x] Affective state of the driver self-reported through the HMI systems.
* Physiological data
  - [x] Temp : Skin temperature (<sup>o</sup>C)
  - [x] EDA : Electrodermal Activity (µS)
  - [x] BVP : photoplethysmograph
  - [x] HR : Average heart rate from BVP signal (bpm)
  - [x] ACC : 3-axis accelerometer on wrist band (1/64g)
* Audio
  - [x] Audio acquired from cavin of vehicle(right side of the driver's seat headrest) (.wav)
