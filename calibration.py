import numpy as np
import cv2
import glob
from os import path

printerName = 'UMS5'
data_path = path.join('data', printerName, 'calibration')

g = (7, 7)
gsize = 0.023  # mm

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((g[0]*g[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:g[0], 0:g[1]].T.reshape(-1, 2)
# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.
images = glob.glob(path.join(data_path, 'image_*.png'))
print(len(images))
for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, g, None)
    # If found, add object points, image points (after refining them)
    if ret is True:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners)
        # Draw and display the corners
        # print(corners2)
        # cv.drawChessboardCorners(img, g, corners2, ret)
        # cv.circle(img, tuple(corners2[3*4, 0]), 30, (0, 255, 0), 2)
        # print(corners2[3*4, 0])
        # cv.imshow('img', img)
        # cv.waitKey(500)

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

print("Camera matrix : \n")
print(mtx)
print("dist : \n")
print(dist)
# print("rvecs : \n")
# print(rvecs)
# print("tvecs : \n")
# print(tvecs)

with open(path.join(data_path, 'intrinsic.npy'), 'wb') as fp:
    np.save(fp, [mtx, dist])

mean_error = 0
for i in range(len(objpoints)):
    imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
    error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2)/len(imgpoints2)
    mean_error += error
print("total error: {}".format(mean_error/len(objpoints)))


###########


img = cv2.imread(path.join(data_path, 'image_ref.png'))
h, w = img.shape[:2]
print(h, w)

# index of the corner that is to be set as new origin
co_idx = 12

g = (4, 7)
objp = np.zeros((g[0]*g[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:g[0], 0:g[1]].T.reshape(-1, 2)
objp -= objp[co_idx]  # take 12th corner as center

axis = np.float32([[3, 0, 0], [0, 3, 0], [0, 0, -3]]).reshape(-1, 3)


def draw(img, corners, imgpts):
    corner = tuple(corners[co_idx].ravel())
    img = cv2.line(img, corner, tuple(imgpts[0].ravel()), (255, 0, 0), 5)
    img = cv2.line(img, corner, tuple(imgpts[1].ravel()), (0, 255, 0), 5)
    img = cv2.line(img, corner, tuple(imgpts[2].ravel()), (0, 0, 255), 5)
    return img


gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ret, corners = cv2.findChessboardCorners(gray, g, None)
if ret is True:
    corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
    # Find the rotation and translation vectors.
    ret, rvecs, tvecs = cv2.solvePnP(objp, corners2, mtx, dist)
    print('===================')

    # Target: Camera pose in printer space (p)
    # P_p: camera pose in printer space
    # P_b: camera pose in checkerboard space
    # P_c: camera pose in camera space
    # P_o: camera pose in camera space of OpenCV

    # P_c = R_o2b P_o
    # P_b = inv(T_b2c R_b2c) T P_c
    # P_p = T_b2p R_b2p P_b

    P_c = np.identity(4)

    # reshape to proper shape
    rvecs = rvecs.reshape((3))
    tvecs = tvecs.reshape((3))
    print(rvecs, tvecs)

    # Rotation from checkerboard sapce to camera space
    R_b2c = np.identity(4)
    R_b2c[:3, :3] = cv2.Rodrigues(rvecs)[0]
    T_b2c = np.identity(4)
    T_b2c[:3, 3] = tvecs * gsize
    print(R_b2c)
    print(T_b2c)

    P_b = np.linalg.inv(T_b2c @ R_b2c) @ P_c
    print(P_b)

    tvec_b2p = [0.15, 0.12, -0.132]

    # rotate along x-axis by 180 deg
    R_b2p = np.identity(4)
    R_b2p[1, 1] = -1
    R_b2p[2, 2] = -1
    T_b2p = np.identity(4)
    T_b2p[:3, 3] = tvec_b2p
    print(R_b2p)
    print(T_b2p)

    P_p = T_b2p @ R_b2p @ P_b
    print(P_p)

    # OpenCV camera coordinate to Blender camera coordinate
    R_o2b = np.array([
        [1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, 0],
        [0, 0, 0, 1]
    ])
    P_blender = P_p @ R_o2b
    print(P_blender)

    with open(path.join(data_path, 'camera_pose.npy'), 'wb') as fp:
        np.save(fp, P_blender)
    print('---')

    # Display
    # project 3D points to image plane
    imgpts, jac = cv2.projectPoints(axis, rvecs, tvecs, mtx, dist)
    img = draw(img, corners2, imgpts)
    cv2.imshow('img', img)
    k = cv2.waitKey(0) & 0xFF
