import argparse
import pathlib
import pickle
import time
from datetime import datetime
from os import makedirs, path

import cv2
import numpy as np

from image_processor import ImageProcessor
from path_manager import PathManager
from simulator import Simulator
from UltimakerPrinter import Printer

# parse argument
parser = argparse.ArgumentParser()
parser.add_argument('--printer', '-p', type=str, required=True, help='Printer name')
args = parser.parse_args()

# printer (specified in ultimaker.ini)
printer_name = args.printer
printer = Printer(printer_name)

# path manager
pm = PathManager(printer_name=printer_name, abs_path=pathlib.Path(__file__).parent.absolute())

while True:
    # check printer state every minute
    print('wait for printing...')
    printerStatus = ''
    printJobState = ''
    waitTime = 60
    while True:
        # check printer status
        if printer.getPrinterState() == 'printing':
            printerStatus = 'printing'
            # check print job state
            if printJobState != printer.getPrintJobState():
                printJobState = printer.getPrintJobState()
                print(printerStatus, printJobState)
                if printJobState == 'printing':
                    break
            waitTime = 1
        else:
            if printerStatus != printer.getPrinterState():
                printerStatus = printer.getPrinterState()
                print(printerStatus)
            waitTime = 60

        time.sleep(waitTime)

    print("start printing!")

    # get print job info
    printJob = printer.getPrintJob()
    date = datetime.now().strftime('%Y%m%d%H%M%S')
    # folderPath = 'data/UM{}/{}_{}/'.format(printer_name, printJob['name'], date)
    pm.setPrintJob('{}_{}'.format(printJob['name'], date))
    # create print job folders
    makedirs(pm.raw_images)

    print(pm.printjob_folder)

    # save printjob information
    with open(pm.printjob_start, 'wb') as fp:
        pickle.dump(printJob, fp)

    # get gcode
    gcode = printer.getPrintJobGcode()
    if gcode is None:
        continue
    with open(pm.gcode, 'w') as fp:
        fp.write(gcode)

    # parse gcode
    sim = Simulator(pm)
    sim.parseGcode()
    # simulate for every layer (async)
    sim_thread = sim.simulate(gen_testing_data=True)

    # image processor
    ip = ImageProcessor()
    if path.exists(pm.intrinsic):
        ip.setCalibrationData(pm.intrinsic)
        makedirs(pm.images)

    # progess file & test list file
    progress_fp = open(pm.raw_progress, 'w')
    test_list_fp = open(pm.test_list, 'w')

    # layer_height = 0
    # queues for detect height change
    queue_hc = []

    # snapshot during printing
    while True:
        print(datetime.now().timestamp())
        # get snaphot
        raw_img = printer.getCameraSnapshot()
        print(datetime.now().timestamp())
        # current progress and time
        progress = printer.getPrintJobProgress()
        position = printer.getPrinterHeadPosition()
        timestamp = datetime.now().timestamp()
        print(timestamp, progress, position)

        if raw_img is not None and progress is not None and position is not None and not np.isnan(position).any():
            # preprocessing (include save raw image)
            filename = '{}.png'.format(str(timestamp))
            img = ip.preprocess(raw_img, path.join(pm.raw_images, filename))

            # check image validity
            if img is not None:
                # collect training data
                cv2.imwrite(path.join(pm.images, filename), img)
                progress_fp.write('{}, {}, {}\n'.format(timestamp, progress, position))

                # FIXME: detect failure every layer
                queue_hc.append([np.round(position[2], decimals=2), timestamp])
                if len(queue_hc) > 4:
                    queue_hc.pop(0)

                queue_tmp = np.array(queue_hc)
                if len(queue_tmp) >= 4 and queue_tmp[0, 0] < queue_tmp[1, 0] and (queue_tmp[1, 0] == queue_tmp[2:, 0]).all():
                    layer_height, timestamp = queue_tmp[1]

                    print('Predict at layer height:', layer_height)

                    ''' Failure Detection '''
                    # check if the input and simulation images exist
                    input_path = path.join(pm.images, '{}.png'.format(timestamp))
                    sim_path = path.join(pm.testing, '{}.png'.format(layer_height))
                    # record testing data
                    test_list_fp.write('{}, {}\n'.format(layer_height, timestamp))

                    if path.exists(input_path) and path.exists(sim_path):
                        print('EVALUATE!!')
                        # TODO: load input image image (for testing)
                        # input_img = cv2.imread(input_path)

                        # TODO: load simulated image (for testing)
                        # simulated_img = cv2.imread(sim_path)

                        # TODO: predict
                        # predict_img = model.predict(input_img)

                        # TODO: evaluate
                        # score = evaluate(predict_img, simulated_img)

                        # TODO: alert if fall
                        # if score < threshold:
                        #     print('[Printing Error] probrary fail')
            else:
                print('Invalid input image')

        # check progress and print job state
        printJobState = printer.getPrintJobState()
        if progress == 1 or (printJobState != 'printing' and printJobState is not None):
            print(printJobState)
            print('loop break')
            break

        time.sleep(1)

    # progress data & test list file
    progress_fp.close()
    test_list_fp.close()

    # print job
    printJob = printer.getPrintJob()
    with open(pm.printjob_finish, 'wb') as fp:
        pickle.dump(printJob, fp)

    # wait for state change
    while printer.getPrintJobState() == 'printing':
        time.sleep(10)

    # TODO: terminate simulation thread

    print('print finished !')
