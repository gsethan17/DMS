import os
import pyrealsense2 as rs

def receive_realsense(d_name, path, view, position, n_serial, stop_event):
    FPS = 60
    WIDTH = 1280
    HEIGHT = 720

    print(f"[INFO] PID[{os.getpid()}] '{d_name}' process is started.")

    save_path = os.path.join(path, 'video', view, position)

    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    pipe = rs.pipeline()
    config = rs.config()

    config.enable_device(n_serial)
    config.enable_stream(rs.stream.color, WIDTH, HEIGHT, rs.format.bgr8, FPS)
    # config.enable_stream(rs.stream.infrared, 1, 1280, 720, rs.format.y8, fps)
    # config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, fps)

    profile = pipe.start(config)
    try:
        for i in range(0, 100):
            frames = pipe.wait_for_frames()
            for f in frames:
                print(f.profile)
    finally:
        pipe.stop()

def opencv_viewer_exmaple():
    import pyrealsense2 as rs
    import numpy as np
    import cv2

    # Configure depth and color streams
    pipeline = rs.pipeline()
    config = rs.config()

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

    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    if device_product_line == 'L500':
        config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
    else:
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # Start streaming
    pipeline.start(config)

    try:
        while True:

            # Wait for a coherent pair of frames: depth and color
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

            depth_colormap_dim = depth_colormap.shape
            color_colormap_dim = color_image.shape

            # If depth and color resolutions are different, resize color image to match depth image for display
            if depth_colormap_dim != color_colormap_dim:
                resized_color_image = cv2.resize(color_image, dsize=(depth_colormap_dim[1], depth_colormap_dim[0]), interpolation=cv2.INTER_AREA)
                images = np.hstack((resized_color_image, depth_colormap))
            else:
                images = np.hstack((color_image, depth_colormap))

            # Show images
            cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('RealSense', images)
            cv2.waitKey(1)

    finally:

        # Stop streaming
        pipeline.stop()

if __name__ == '__main__':
    # example()
    
    d_name = 'out_video'
    DATASET_PATH = os.getcwd()
    view = 'external'
    position = 'FC'

    receive_realsense(d_name, DATASET_PATH, view, position, '10242207382', None)
    