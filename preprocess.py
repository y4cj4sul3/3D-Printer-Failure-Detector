import cv2
import numpy as np
from glob import glob
from os import path, makedirs, rename

# image size collected from ultimaker printers
H = 600
W = 800

for printer_folder in glob('data/*'):
    cal_folder = path.join(printer_folder, 'calibration')
    if path.exists(cal_folder):
        # printer with calibrated information
        print(printer_folder)

        # load calibration data
        with open(path.join(cal_folder, 'intrinsic.npy'), 'rb') as fp:
            mtx, dist = np.load(fp, allow_pickle=True)
        print(mtx, dist)

        # compute intrinsic matrix
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (W, H), 1, (W, H))

        for printjob_folder in glob(path.join(printer_folder, '*')):
            if path.exists(path.join(printjob_folder, 'printjob_finish.pkl')) and not path.exists(path.join(printjob_folder, 'undistorted')):
                # completely recorded printjobs
                print(printjob_folder)

                # create temp folder
                temp_folder = path.join(printjob_folder, 'temp')
                if not path.exists(temp_folder):
                    makedirs(temp_folder)

                # create folder for abandoned images
                abandon_folder = path.join(printjob_folder, 'abandon')
                if not path.exists(abandon_folder):
                    makedirs(abandon_folder)

                # undistortion
                for filepath in glob(path.join(printjob_folder, 'images/*.png')):
                    img = cv2.imread(filepath)

                    # check if the image file is valid
                    # the checked area is not necessary to be exact the last row
                    if (img[-1, :, :] == 128).all():
                        # image invalid, move to abandon folder
                        # print(filepath)
                        rename(filepath, path.join(abandon_folder, path.basename(filepath)))
                        continue

                    # image size check
                    h, w = img.shape[:2]
                    if h != H or w != W:
                        continue

                    # undistort
                    dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
                    # crop the image
                    x, y, w, h = roi
                    dst = dst[y:y+h, x:x+w]

                    cv2.imwrite(path.join(temp_folder, path.basename(filepath)), dst)

                # rename temp folder
                rename(path.join(printjob_folder, 'temp'), path.join(printjob_folder, 'undistorted'))

# reload to verify and also preprocess progress file
# if no error message 'Corrupt JPEG data: premature end of data segment' from opencv
# then everything is fine
print('\n\n================ VERIFY ================')

for printer_folder in glob('data/*'):
    if path.exists(path.join(printer_folder, 'calibration')):
        for printjob_folder in glob(path.join(printer_folder, '*')):
            if path.exists(path.join(printjob_folder, 'undistorted')):
                print(printjob_folder)

                # load progress file
                fp_r = open(path.join(printjob_folder, 'progress.txt'), 'r')
                fp_w = open(path.join(printjob_folder, 'new_progress.txt'), 'w')
                timestamp = ''

                for filepath in sorted(glob(path.join(printjob_folder, 'images/*.png'))):
                    # load to check if the image is valid
                    img = cv2.imread(filepath)

                    filename = path.splitext(path.basename(filepath))[0]

                    # skip nonexisting images
                    while timestamp != filename:
                        line = fp_r.readline()
                        data = line.split(', ')
                        timestamp = data[0]

                    # check data validity
                    if len(data) == 5 and not np.isnan([float(data[2][1:]), float(data[3]), float(data[4][:-2])]).any():
                        fp_w.write(line)

                fp_r.close()
                fp_w.close()
