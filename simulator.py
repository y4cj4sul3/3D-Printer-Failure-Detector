import pathlib
import subprocess
from path_manager import PathManager
from gcode_parser import GcodeParser
import time
import numpy as np
from threading import Thread


class Simulator:
    def __init__(self, pm: PathManager):
        self.pm = pm

    def parseGcode(self):

        then = time.time()

        # load and parse file
        parser = GcodeParser()
        model = parser.parseFile(self.pm.gcode)
        model.subdivide(1)
        # convert to mesh data
        model.classifySegments()
        verts, edges, time_height = model.draw()

        now = time.time()

        # save model
        with open(self.pm.model, 'wb') as fp:
            np.save(fp, [verts, edges, time_height])

        # print('then', then)
        print("importing Gcode took", now-then)

    def simulate(self, background=True, gen_training_data=False, gen_testing_data=False, asynchronous=True):

        if self.pm.abs_path is not None:
            # run blender
            # FIXME: run_blender.py path
            cmd = ['blender', '--python', 'run_blender.py', '--']
            cmd += ['--project-path', self.pm.abs_path]
            cmd += ['--printer', self.pm.printer_name]
            cmd += ['--printjob', self.pm.printjob_name]

            # run in background
            if background:
                cmd.insert(1, '--background')
            # generate training data
            if gen_training_data:
                cmd.append('--gen-training-data')
            # generate testing data
            if gen_testing_data:
                cmd.append('--gen-testing-data')

            if asynchronous:
                thread = Thread(target=self._exeCmd, args=(cmd,))
                thread.start()
                return thread
            else:
                self._exeCmd(cmd)

        else:
            print('Absolute path is required')

        return None

    def _exeCmd(self, cmd):
        print(cmd)
        subprocess.run(cmd)
        print('Simulation finished')


if __name__ == "__main__":

    ''' Offline Simulation '''
    from os import path

    pm = PathManager(abs_path=pathlib.Path(__file__).parent.absolute())

    # generate training data
    for printer_name in pm.getPrinterNames():
        pm.setPrinter(printer_name)
        if path.exists(pm.calibration_folder):
            for printjob_name in pm.getPrintJobNames():
                pm.setPrintJob(printjob_name)
                if path.exists(pm.images):
                    print(pm.printjob_folder)

                    sim = Simulator(pm)

                    sim.parseGcode()

                    sim.simulate(gen_training_data=True)

