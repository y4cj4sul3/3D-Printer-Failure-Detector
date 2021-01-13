from os import path, makedirs
import pathlib
import numpy as np

from path_manager import PathManager
from segmentation import Evaluator
from visualization_client import DetectorVisualizerClient

# path manager
pm = PathManager(abs_path=pathlib.Path(__file__).parent.absolute(), printer_name='S5', printjob_name='UMS5_4064a7f6-d290-485e-83ca-373373bebcae_20210111154854')
# evaluator
evaluator = Evaluator('segmentation/model/PAN-se_resnet50-aug-best_model-traced.pth')
# visualizer
vc = DetectorVisualizerClient(pm.printer_name + ' (Offline)')
vc.sendPrinterInfo(printjob_name=pm.printjob_name)

if not path.exists(pm.seg_images):
    makedirs(pm.seg_images)
if not path.exists(pm.iou_images):
    makedirs(pm.iou_images)
if not path.exists(pm.blend_images):
    makedirs(pm.blend_images)

eval_result_fp = open(pm.eval_result, 'w')
iou_list = [1.0 for _ in range(10)]

with open(pm.test_list, 'r') as fp:
    for line in fp.readlines():
        lh, ts = line.split(', ')

        input_path = path.join(pm.images, f'{ts[:-1]}.png')
        sim_path = path.join(pm.testing, f'{lh}.png')

        if path.exists(input_path) and path.exists(sim_path):

            seg_path = path.join(pm.seg_images, f'{lh}.png')
            iou_path = path.join(pm.iou_images, f'{lh}.png')
            blend_path = path.join(pm.blend_images, f'{lh}.png')

            loss, iou = evaluator.evaluate(pm.abs(input_path), pm.abs(sim_path), pm.abs(seg_path), pm.abs(iou_path), pm.abs(blend_path))
            eval_result_fp.write(f'{lh}, {loss}, {iou}\n')

            iou_list.append(iou)
            iou_list.pop(0)
            smooth_iou = np.mean(iou_list)
            print(f" === Height: {lh}, Loss: {loss}, IOU: {iou}, Smoothed IOU: {smooth_iou} === ")

            vc.sendPrinterInfo(input_img_path=input_path, sim_img_path=sim_path, predict_img_path=seg_path, iou_img_path=iou_path, blend_img_path=blend_path, result=f'{loss},{iou},{smooth_iou}')
