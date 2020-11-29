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
    with open(folderPath + 'path.gcode', 'w') as fp:
        fp.write(gcode)

    progress = []
    timestamp = []
    # snapshot during printing
    while True:
        # current progress and time
        progress.append(printer.getPrintJobProgress())
        timestamp.append(datetime.now().timestamp())
        print(timestamp[-1], progress[-1])
        # get snaphot
        img = printer.getCameraSnapshot()
        if img is not None and progress[-1] is not None:
            with open(folderPath + 'images/' + str(timestamp[-1]) + '.png', 'wb') as fp:
                shutil.copyfileobj(img, fp)
                
        if progress[-1] == 1:
            break

    # progress data
    progress_data = {
        'timestamp': timestamp,
        'progress': progress
    }
    with open(folderPath + 'progress.pkl', 'wb') as fp:
        pickle.dump(progress_data, fp)

    # print job
    printJob = printer.getPrintJob()
    with open(folderPath + 'printJob_finish.pkl', 'wb') as fp:
        pickle.dump(printJob, fp)

    # wait for state change
    while printer.getPrintJobState() == 'printing':
        time.sleep(10)

    print('print finished !')

