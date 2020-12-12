import os
import pickle
import shutil

import time
from datetime import datetime

import argparse

from UltimakerPrinter import Printer

# parse argument
parser = argparse.ArgumentParser()
parser.add_argument('--printer', '-p', type=str, required=True, help='Printer name')
args = parser.parse_args()

# printer (specified in ultimaker.ini)
printerName = args.printer
printer = Printer(printerName)

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
    folderPath = 'data/UM{}/{}_{}/'.format(printerName, printJob['name'], date)
    os.makedirs(folderPath + 'images/')
    print(folderPath)
    with open(folderPath + 'printJob_start.pkl', 'wb') as fp:
        pickle.dump(printJob, fp)

    # get gcode
    gcode = printer.getPrintJobGcode()
    if gcode is None:
        continue
    with open(folderPath + 'path.gcode', 'w') as fp:
        fp.write(gcode)

    # progess file
    progress_fp = open(folderPath + 'progress.txt', 'w')

    #progress = []
    #timestamp = []
    # snapshot during printing
    while True:
        print(datetime.now().timestamp())
        # get snaphot
        img = printer.getCameraSnapshot()
        print(datetime.now().timestamp())
        # current progress and time
        progress = printer.getPrintJobProgress()
        head_position = printer.getPrinterHeadPosition()
        timestamp = datetime.now().timestamp()
        print(timestamp, progress, head_position)

        if img is not None and progress is not None:
            # save to file
            progress_fp.write('{}, {}, {}\n'.format(timestamp, progress, head_position))
            with open(folderPath + 'images/' + str(timestamp) + '.png', 'wb') as fp:
                shutil.copyfileobj(img, fp)
                
        # check progress and print job state
        printJobState = printer.getPrintJobState()
        if progress == 1 or (printJobState != 'printing' and printJobState is not None):
            print(printJobState)
            print('loop break')
            break

        time.sleep(1)

    # progress data
    progress_fp.close()
    # progress_data = {
    #     'timestamp': timestamp,
    #     'progress': progress
    # }
    # with open(folderPath + 'progress.pkl', 'wb') as fp:
    #     pickle.dump(progress_data, fp)

    # print job
    printJob = printer.getPrintJob()
    with open(folderPath + 'printJob_finish.pkl', 'wb') as fp:
        pickle.dump(printJob, fp)

    # wait for state change
    while printer.getPrintJobState() == 'printing':
        time.sleep(10)

    print('print finished !')

