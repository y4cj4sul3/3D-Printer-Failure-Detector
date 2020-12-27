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

                # undistortion
                for filepath in glob(path.join(printjob_folder, 'images/*.png')):
                    # TODO: check if the image file is valid
                    img = cv2.imread(filepath)

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
