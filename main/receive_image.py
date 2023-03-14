import os
import pyrealsense2 as rs
import pyrealsense2 as rs
import numpy as np
import cv2
import time



def receive_realsense(d_name, save_flag, path, view, position, n_serial, fps, width, height, stop_event):
    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")

    save_path = os.path.join(path, 'video', view, position)

    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    FPS = fps
    WIDTH = width
    HEIGHT = height
    # n_serial = "043322071182"

    # Configure depth and color streams
    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_device(n_serial)
    # config.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)
    # config.enable_device("043322071182")

    # Get device product line for setting a supporting resolution
    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()
    device_product_line = str(device.get_info(rs.camera_info.product_line))

    found_rgb = False
    for s in device.sensors:
        if s.get_info(rs.camera_info.name) == 'RGB Camera':
            found_rgb = True
            break
    if not found_rgb:
        print("The demo requires Depth camera with Color sensor")
        exit(0)

    # \config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    # config.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)

    if device_product_line == 'L500':
        config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
    else:
        config.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)
        if view == 'internal':
            config.enable_stream(rs.stream.infrared, 1, WIDTH, HEIGHT, rs.format.y8, FPS)

    # Start streaming
    pipeline.start(config)

    try:
        while True:

            # Wait for a coherent pair of frames: depth and color
            frames = pipeline.wait_for_frames()
            cur_time = time.time()

            color_frame = frames.get_color_frame()
            if view == 'internal':
                # depth_frame = frames.get_depth_frame()
                ir_frame = frames.get_infrared_frame()
            else:
                ir_frame = True

            if not ir_frame or not color_frame:
                continue

            # Convert images to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())
            if view == 'internal':
                ir_image = np.asanyarray(ir_frame.get_data())
            # depth_image = np.asanyarray(depth_frame.get_data())

            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
            # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
            if view == 'internal':
                ir_image = cv2.cvtColor(ir_image, cv2.COLOR_GRAY2BGR)

            # depth_colormap_dim = depth_colormap.shape
            # color_colormap_dim = color_image.shape

            # If depth and color resolutions are different, resize color image to match depth image for display
            # if depth_colormap_dim != color_colormap_dim:
                # resized_color_image = cv2.resize(color_image, dsize=(depth_colormap_dim[1], depth_colormap_dim[0]), interpolation=cv2.INTER_AREA)
                # images = np.hstack((resized_color_image, depth_colormap))
            # else:
                # images = np.hstack

            # Save images
            cv2.imwrite(os.path.join(save_path, f"{cur_time}.png"), color_image)
            if view == 'internal':
                cv2.imwrite(os.path.join(save_path, f"{cur_time}_ir.png"), ir_image)

            # Show images
            resize_img = cv2.resize(color_image, (640, 480))

            cv2.namedWindow('{}_{}'.format(view, position), cv2.WINDOW_AUTOSIZE)
            cv2.imshow('RealSense', resize_img)
            
            if view == 'internal':
                resize_img_ir = cv2.resize(ir_image, (640, 480))
                cv2.namedWindow('{}_{}_{}'.format(view, position, 'IR'), cv2.WINDOW_AUTOSIZE)
                cv2.imshow('RealSense', resize_img_ir)
            cv2.waitKey(1)

            if stop_event:
                if stop_event.is_set():
                    break

    finally:

        # Stop streaming
        pipeline.stop()
        print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is terminated.")


if __name__ == '__main__':

    realsense_ctx = rs.context()  # The context encapsulates all of the devices and sensors, and provides some additional functionalities.
    connected_devices = []

    # get serial numbers of connected devices:
    for i in range(len(realsense_ctx.devices)):
        detected_camera = realsense_ctx.devices[i].get_info(
        rs.camera_info.serial_number)
        connected_devices.append(detected_camera)

    print(connected_devices)

    save_flag = True
    d_name = 'out_video'
    DATASET_PATH = os.getcwd()
    view = 'external'
    position = 'FC'

    receive_realsense(d_name, save_flag, DATASET_PATH, view, position, '102422073082', None)
