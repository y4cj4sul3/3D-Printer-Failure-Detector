from os import path
from glob import glob


class PathManager:
    def __init__(self, abs_path=None, data_folder='data', printer_name=None, printjob_name=None):
        # absolute path to the data folder (exclude data folder)
        self.abs_path = abs_path
        # data folder, relative path to data folder
        self.data_folder = data_folder

        # current printer
        self.setPrinter(printer_name)
        # current printjob
        self.setPrintJob(printjob_name)

    def setPrinter(self, printer_name):
        if type(printer_name) == str and len(printer_name) > 0:
            # printer name, same as specified in ultimaker.ini
            self.printer_name = printer_name
            # printer folder: data/UM?/
            self.printer_folder = path.join(self.data_folder, 'UM' + self.printer_name)

            # caliration: data/UM?/calibration/
            self.calibration_folder = path.join(self.printer_folder, 'calibration')
            # calibration images: data/UM?/calibration/images/
            self.cal_images = path.join(self.calibration_folder, 'images')
            # reference calibration image: data/UM?/calibration/images/ref.png
            self.ref_images = path.join(self.cal_images, 'ref.png')
            # intrinsic parameters: data/UM?/calibration/intrinsic.npy
            self.intrinsic = path.join(self.calibration_folder, 'intrinsic.npy')
            # camera pose: data/UM?/calibration/camera_pose
            self.camera_pos = path.join(self.calibration_folder, 'camera_pose.npy')
        else:
            self.printer_name = None
            self.printer_folder = None

            self.calibration_folder = None
            self.cal_images = None
            self.ref_images = None
            self.intrinsic = None
            self.camera_pos = None

        # reset printjob
        self.setPrintJob(None)

    def setPrintJob(self, printjob_name):
        if type(printjob_name) == str and len(printjob_name) > 0:
            # printjob name
            self.printjob_name = printjob_name
            # printjob folder: data/UM?/<printjob>/
            self.printjob_folder = path.join(self.printer_folder, printjob_name)

            # raw images folder: data/UM?/<printjob>/raw_images/
            self.raw_images = path.join(self.printjob_folder, 'raw_images')
            # images folder: data/UM?/<printjob>/images/
            self.images = path.join(self.printjob_folder, 'images')
            # abandon images folder: data/UM?/<printjob>/abandon/
            self.abandon_images = path.join(self.printjob_folder, 'abandon')

            # simulated images folder: data/UM?/<printjob>/simulation/
            self.simulation = path.join(self.printjob_folder, 'simulation')
            # training data folder: data/UM?/<printjob>/simulation/training/
            self.training = path.join(self.simulation, 'training')
            # testing data folder: data/UM?/<printjob>/simulation/testing/
            self.testing = path.join(self.simulation, 'testing')

            # gcode: data/UM?/<printjob>/path.gcode
            self.gcode = path.join(self.printjob_folder, 'path.gcode')
            # model: data/UM?/<printjob>/model.npy
            self.model = path.join(self.printjob_folder, 'model.npy')

            # printjob info (start): data/UM?/<printjob>/printjob_start.pkl
            self.printjob_start = path.join(self.printjob_folder, 'printjob_start.pkl')
            # printjob info (finish): data/UM?/<printjob>/printjob_finish.pkl
            self.printjob_finish = path.join(self.printjob_folder, 'printjob_finish.pkl')

            # raw_progress: data/UM?/<printjob>/raw_progress.txt
            self.raw_progress = path.join(self.printjob_folder, 'raw_progress.txt')
            # progress: data/UM?/<printjob>/progress.txt
            self.progress = path.join(self.printjob_folder, 'progress.txt')

            # testing data list: data/UM?/<printjob>/test_list.txt
            self.test_list = path.join(self.printjob_folder, 'test_list.txt')

        else:
            self.printjob_name = None
            self.printjob_folder = None

            self.raw_images = None
            self.images = None
            self.abandon_images = None

            self.simulation = None
            self.training = None
            self.testing = None

            self.gcode = None
            self.model = None

            self.printjob_start = None
            self.printjob_finish = None

            self.raw_progress = None
            self.progress = None

            self.test_list = None

    def abs(self, rel_path):
        if self.abs_path is None:
            print('Invalid absolute path. Please specify abs_path when initialize PathManager.')
            return None
        elif path is None:
            print('Invalid path')
            return None
        else:
            return path.join(self.abs_path, rel_path)

    def getPrinterNames(self):
        printer_folders = glob(path.join(self.data_folder, 'UM*'))
        printer_names = [path.basename(x)[2:] for x in printer_folders]
        return printer_names

    def getPrintJobNames(self):
        printjob_folders = glob(path.join(self.printer_folder, '*'))
        printjob_names = [path.basename(x) for x in printjob_folders]
        return printjob_names


if __name__ == '__main__':
    pm = PathManager()

    for printer_name in pm.getPrinterNames():
        print(printer_name)
        pm.setPrinter(printer_name)
        for printjob_name in pm.getPrintJobNames():
            print(printjob_name)
