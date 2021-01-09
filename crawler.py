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
from segmentation import Evaluator
from visualization_client import DetectorVisualizerClient

# parse argument
parser = argparse.ArgumentParser()
parser.add_argument('--printer', '-p', type=str, required=True, help='Printer name')
parser.add_argument('--simulate', '-s', action='store_true', help='Simulate printing process')
parser.add_argument('--evaluate', '-e', action='store_true', help='Simulate printing process')
parser.add_argument('--visualizer', '-v', action='store_true', help='Visualize result')
args = parser.parse_args()
# arguments
printer_name = args.printer
do_simulate = args.simulate
do_evaluate = args.evaluate
if do_evaluate:
    do_simulate = True
do_visualize = args.visualizer

# printer (specified in ultimaker.ini)
printer = Printer(printer_name)

# path manager
pm = PathManager(printer_name=printer_name, abs_path=pathlib.Path(__file__).parent.absolute())

# evaluator
evaluator = None
if do_evaluate:
    # create folder
    # load evaluation model
    evaluator = Evaluator('segmentation/model/PAN-se_resnet50-aug-best_model-traced.pth')
# visualizer
vc = None
if do_visualize:
    vc = DetectorVisualizerClient(pm.printer_name)

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
                if do_visualize:
                    vc.sendPrinterInfo(printer_state=printerStatus, printjob_state=printJobState)
                if printJobState == 'printing':
                    break
            waitTime = 1
        else:
            if printerStatus != printer.getPrinterState():
                printerStatus = printer.getPrinterState()
                print(printerStatus)
                if do_visualize:
                    vc.sendPrinterInfo(printer_state=printerStatus)

            waitTime = 60

        time.sleep(waitTime)

    print("start printing!")

    # get print job info
    printJob = printer.getPrintJob()
    date = datetime.now().strftime('%Y%m%d%H%M%S')
    # folderPath = 'data/UM{}/{}_{}/'.format(printer_name, printJob['name'], date)
    pm.setPrintJob(f'{printJob["name"]}_{date}')
    # create print job folders
    makedirs(pm.raw_images)

    print(pm.printjob_folder)

    if do_visualize:
        vc.sendPrinterInfo(printjob_name=pm.printjob_name)

    # save printjob information
    with open(pm.printjob_start, 'wb') as fp:
        pickle.dump(printJob, fp)

    # get gcode
    gcode = printer.getPrintJobGcode()
    if gcode is None:
        continue
    with open(pm.gcode, 'w') as fp:
        fp.write(gcode)

    # simulation
    if do_simulate:
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

    # evaluation
    # layer_height = 0
    # queues for detect height change
    queue_hc = []
    eval_result_fp = None
    if do_evaluate:
        if not path.exists(pm.seg_images):
            makedirs(pm.seg_images)
        eval_result_fp = open(pm.eval_result, 'w')

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
                progress_fp.write(f'{timestamp}, {progress}, {position}\n')

                # evaluation
                if do_evaluate:
                    # detect failure every layer
                    queue_hc.append([np.round(position[2], decimals=2), timestamp])
                    if len(queue_hc) > 4:
                        queue_hc.pop(0)

                    queue_tmp = np.array(queue_hc)
                    if len(queue_tmp) >= 4 and queue_tmp[0, 0] < queue_tmp[1, 0] and (queue_tmp[1, 0] == queue_tmp[2:, 0]).all():
                        layer_height, timestamp = queue_tmp[1]

                        print('Predict at layer height:', layer_height)

                        ''' Failure Detection '''
                        # check if the input and simulation images exist
                        input_path = path.join(pm.images, f'{timestamp}.png')
                        sim_path = path.join(pm.testing, f'{layer_height}.png')
                        # record testing data
                        test_list_fp.write(f'{layer_height}, {timestamp}\n')

                        if path.exists(input_path) and path.exists(sim_path):
                            print('EVALUATE!!')

                            # evaluation
                            seg_path = path.join(pm.seg_images, f'{layer_height}.png')
                            iou_path = path.join(pm.iou_images, f'{layer_height}.png')
                            blend_path = path.join(pm.blend_images, f'{layer_height}.png')
                            loss, iou = evaluator.evaluate(pm.abs(input_path), pm.abs(sim_path), pm.abs(seg_path), pm.abs(iou_path), pm.abs(blend_path))

                            eval_result_fp.write(f'{layer_height}, {loss}, {iou}\n')
                            print(f" === Loss: {loss}, IOU: {iou} === ")

                            if do_visualize:
                                vc.sendPrinterInfo(input_img_path=input_path, sim_img_path=sim_path)
            else:
                print('Invalid input image')

        # check progress and print job state
        printJobState = printer.getPrintJobState()
        if progress == 1 or (printJobState != 'printing' and printJobState is not None):
            print(printJobState)
            print('loop break')
            if do_visualize:
                vc.sendPrinterInfo(printjob_state=printJobState)
            break

        time.sleep(1)

    # FIXME: is the state is pausing, than should wait for resume
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
