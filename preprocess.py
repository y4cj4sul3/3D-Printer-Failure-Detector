'''
Preprocessing for Training Data
'''

from glob import glob
from os import makedirs, path, rename

import cv2
import numpy as np

from image_processor import ImageProcessor
from path_manager import PathManager

pm = PathManager()

# Preprocess raw images
# filter invaliad images and undistort raw images
# Note that this is should already done in clawer when collecting data.
for printer_name in pm.getPrinterNames():
    pm.setPrinter(printer_name)

    if path.exists(pm.calibration_folder):
        # printer with calibrated information
        print(pm.printer_folder)

        # load calibration data
        ip = ImageProcessor(pm.intrinsic)

        for printjob_name in pm.getPrintJobNames():
            pm.setPrintJob(printjob_name)
            if path.exists(pm.printjob_finish) and not path.exists(pm.images):
                # completely recorded printjobs
                print(pm.printjob_folder)

                # create temp folder
                temp_folder = path.join(pm.printjob_folder, 'temp')
                if not path.exists(temp_folder):
                    makedirs(temp_folder)

                # create folder for abandoned images
                if not path.exists(pm.abandon_images):
                    makedirs(pm.abandon_images)

                # undistortion
                for filepath in glob(path.join(pm.raw_images, '*.png')):
                    img = cv2.imread(filepath)

                    # check if the image file is valid
                    # the checked area is not necessary to be exact the last row
                    if not ip.verifyRawImage(img):
                        # image invalid, move to abandon folder
                        # print(filepath)
                        rename(filepath, path.join(pm.abandon_images, path.basename(filepath)))
                        continue

                    dst = ip.undistort(img)

                    cv2.imwrite(path.join(temp_folder, path.basename(filepath)), dst)

                # rename temp folder
                rename(temp_folder, pm.images)

# reload to verify and also preprocess progress file and generate offline testing data list
# if no error message 'Corrupt JPEG data: premature end of data segment' from opencv
# then everything is fine
print('\n\n================ VERIFY ================')

for printer_name in pm.getPrinterNames():
    pm.setPrinter(printer_name)
    if path.exists(pm.calibration_folder):
        for printjob_name in pm.getPrintJobNames():
            pm.setPrintJob(printjob_name)
            if path.exists(pm.images) and not path.exists(pm.progress):
                print(pm.printjob_folder)

                # open raw progress
                fp_r = open(pm.raw_progress, 'r')

                timestamp = ''
                timestamps = []
                position = []
                lines = []
                for filepath in sorted(glob(path.join(pm.images, '*.png'))):
                    # load to check if the image is valid
                    img = cv2.imread(filepath)

                    filename = path.splitext(path.basename(filepath))[0]

                    # skip nonexisting images
                    line = None
                    data = None
                    while timestamp != filename:
                        line = fp_r.readline()
                        data = line.split(', ')
                        timestamp = data[0]

                    # check data validity
                    if len(data) == 5:
                        pos = [float(data[2][1:]), float(data[3]), float(data[4][:-2])]
                        if not np.isnan(pos).any():
                            timestamps.append(timestamp)
                            position.append(pos)
                            lines.append(line)

                position = np.array(position)

                # check initial layer height ascending
                start_idx = 0
                init_height = position[0, 2]
                for pos in position:
                    if init_height > pos[2]:
                        break
                    elif init_height < pos[2]:
                        start_idx = 0
                        break
                    start_idx += 1

                print('Start index:', start_idx)

                with open(path.join(pm.progress), 'w') as fp_w:
                    fp_w.writelines(lines)

                position[:, 2] = np.round(position[:, 2], decimals=2)

                fp_w = open(path.join(pm.test_list), 'w')

                # generate testing data list
                layer_height = position[start_idx, 2]
                for i in range(start_idx+1, len(position)-2):
                    # only when layer height increases
                    if position[i-1, 2] < position[i, 2] and (position[i, 2] == position[i+1:i+3, 2]).all():
                        # print(i, position[i-1:i+2, 2])

                        if layer_height < position[i, 2]:
                            layer_height = position[i, 2]
                            fp_w.write('{}, {}\n'.format(position[i, 2], timestamps[i]))
                        else:
                            print('wrong!')

                fp_w.close()
