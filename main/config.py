config = {'SAVE_PATH': '/media/imlab/Samsung_T5/dms_rev1/',
          'VERSION': 'v1.1.0',
          'DRIVER_LIST': ["Sejoon", "Geesung", "Taesan", "Euiseok",\
                          "Hyeongoo", "Rakcheol", "Youngjun"],
          'CAN': {'inference': False,
                  'print_can_status': True},
          'GNSS': {'trf_info_request_period': 10.0,

                    # '''
                    # If you want to print GNSS status,
                    # set 'print_can_status' to False first.
                    # '''
                   'print_gnss_status': False},

          'external_video': {'show': True},

          # '''
          # Set False if you do not want to collect specific data.
          # '''
          'DATA': {'HMI': False,
                   'CAN': True,
                   'INSIDE_FRONT_CAMERA': False,
                   'INSIDE_SIDE_CAMERA': False,
                   'OUTSIDE_FRONT_CENTER_CAMERA': True,
                   'audio': False,
                   'GNSS' : True,
                  #  '''
                  #  TRAFFIC_INFO must be collected with GNSS
                  #  '''
                   'TRAFFIC_INFO': True,
          },

          'MEASUREMENT': True
}
