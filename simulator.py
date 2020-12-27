import subprocess
import pathlib
import os

# absolute path
filepath = os.path.join(pathlib.Path().absolute(), 'data/UMS5/<YOUR_DATA_FOLDER>')

# run blender
subprocess.run(['blender', '--python', 'run_blender.py', '--', filepath])
