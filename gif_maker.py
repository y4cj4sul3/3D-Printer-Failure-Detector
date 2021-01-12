from glob import glob
import imageio
from os import path

from path_manager import PathManager

pm = PathManager(printer_name='S5', printjob_name='UMS5_test_handle_20210110163551')

imgs = []
lhs = []
with open(pm.test_list, 'r') as fp:
    for line in fp.readlines():
        lh, ts = line.split(', ')
        imgs.append(imageio.imread(path.join(pm.images, f'{ts[:-1]}.png')))
        lhs.append(lh)

imageio.mimsave(path.join(pm.printjob_folder, 'imgs.gif'), imgs)


def makeGIF(input_path, output_name):
    imgs = []
    for lh in lhs:
        imgs.append(imageio.imread(path.join(input_path, f'{lh}.png')))
    imageio.mimsave(path.join(pm.printjob_folder, f'{output_name}.gif'), imgs)


makeGIF(pm.testing, 'sims')
makeGIF(pm.seg_images, 'segs')
# makeGIF(pm.iou_images, 'iou')
# makeGIF(pm.blend_images, 'blend')
