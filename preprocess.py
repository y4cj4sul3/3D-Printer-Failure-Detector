import cv2
import numpy as np
from glob import glob
from os import path, makedirs, rename
from image_processor import ImageProcessor
from path_manager import PathManager

pm = PathManager()

# image size collected from ultimaker printers
# H = 600
# W = 800

for printer_name in pm.getPrinterNames():
    pm.setPrinter(printer_name)

    if path.exists(pm.calibration_folder):
        # printer with calibrated information
        print(pm.printer_folder)

        # load calibration data
        ip = ImageProcessor(pm.intrinsic)

        # with open(path.join(cal_folder, 'intrinsic.npy'), 'rb') as fp:
        #     mtx, dist = np.load(fp, allow_pickle=True)
        # print(mtx, dist)

        # # compute intrinsic matrix
        # newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (W, H), 1, (W, H))

        for printjob_name in pm.getPrintJobNames():
            pm.setPrintJob(printjob_name)
            if path.exists(pm.printjob_finish) and not path.exists(pm.images):
                # completely recorded printjobs
                print(pm.printer_folder)

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
                    # # image size check
                    # h, w = img.shape[:2]
                    # if h != H or w != W:
                    #     continue

                    # # undistort
                    # dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
                    # # crop the image
                    # x, y, w, h = roi
                    # dst = dst[y:y+h, x:x+w]

                    cv2.imwrite(path.join(temp_folder, path.basename(filepath)), dst)

                # rename temp folder
                rename(temp_folder, pm.images)

# reload to verify and also preprocess progress file
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

                # load progress file
                fp_r = open(pm.raw_progress, 'r')
                fp_w = open(pm.progress, 'w')
                timestamp = ''

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

                    # TODO: check layer height ascending

                    # check data validity
                    if len(data) == 5 and not np.isnan([float(data[2][1:]), float(data[3]), float(data[4][:-2])]).any():
                        fp_w.write(line)

                fp_r.close()
                fp_w.close()
