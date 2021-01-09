import shutil
from os import path

import cv2
import numpy as np


class ImageProcessor:
    def __init__(self, cal_path=None, H=600, W=800):
        # raw image size
        self.H = H
        self.W = W

        # set calibration data
        if type(cal_path) == str:
            self.setCalibrationData(cal_path)
        else:
            self.cal_available = False

    def preprocess(self, raw_img, raw_path='tmp.png', **kargs):
        '''
        Preprocess raw image receive from http request.
        Preprocessing includes converting to array type, image verification, and undistortion.
        Conversion will save and reload the image. The raw image will be saved if raw_path is provided.
        '''
        if raw_img is None:
            return None

        # save image
        with open(raw_path, 'wb') as fp:
            shutil.copyfileobj(raw_img, fp)
        # reload image
        img = cv2.imread(raw_path)

        # verify and undistort image
        if self.verifyRawImage(img, **kargs) and self.cal_available:
            return self.undistort(img)
        else:
            return None

    def verifyRawImage(self, img, rows=1, cols=0):
        '''
        Check whether the image file is valid
        If the lower part of the image is al gray (128),
        then it is very possible to be a invalid image
        The checked area is not necessary to be exact the last row.
        img: RGB image, numpy array
        rows, cols: the area to be checked, anchored at bottom right, set 0 to check all
        '''
        try:
            return not (img[-rows:, -cols:, :] == 128).all()
        except TypeError:
            print('TypeError: ', type(img), np.shape(img))
            return False

    def setCalibrationData(self, cal_path: str):
        if path.exists(cal_path):
            # load calibration data (intrinsic)
            with open(cal_path, 'rb') as fp:
                mtx, dist = np.load(fp, allow_pickle=True)

            print(mtx, dist)
            self.mtx = mtx
            self.dist = dist

            # compute intrinsic matrix
            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (self.W, self.H), 1, (self.W, self.H))
            self.intrinsic = newcameramtx
            self.roi = roi

            self.cal_available = True

        else:
            print('Invalid calibration data path.')
            self.cal_available = False

    def undistort(self, img):
        if not self.cal_available:
            print('Calibration data does not exist. Please set calibration data first.')
            return None

        # image size check
        h, w = img.shape[:2]
        if h != self.H or w != self.W:
            return None

        # undistort
        dst = cv2.undistort(img, self.mtx, self.dist, None, self.intrinsic)
        # crop the image
        x, y, w, h = self.roi
        dst = dst[y:y+h, x:x+w]

        return dst
