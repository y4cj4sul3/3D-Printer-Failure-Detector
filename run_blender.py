import bpy
from sys import argv
from os import path

# get file path
filepath = argv[4]

bpy.ops.threedpfd.all_in_one(filepath=filepath)

# config_path = path.join('/'.join(filepath.split('/')[:-1]), 'calibration/camera_pose.npy')
# bpy.ops.threedpfd.setup_scene(filepath=config_path)
