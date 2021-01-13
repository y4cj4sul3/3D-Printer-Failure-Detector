from os import path

import imageio

from path_manager import PathManager

pm = PathManager(printer_name='S5', printjob_name='UMS5_579f7056-b56e-468a-a45f-37a8f0c22d87_20201228185653')

lhs = []
tss = []
with open(pm.test_list, 'r') as fp:
    for line in fp.readlines():
        lh, ts = line.split(', ')
        lhs.append(lh)
        tss.append(ts[:-1])


def makeGIF(input_path, file_list, output_name):
    imgs = []
    for filename in file_list:
        imgs.append(imageio.imread(path.join(input_path, f'{filename}.png')))

    output_file = path.join(pm.printjob_folder, f'{output_name}.gif')
    imageio.mimsave(output_file, imgs)
    print(f'Saved: {output_file}')


makeGIF(pm.images, tss, 'imgs')
makeGIF(pm.raw_images, tss, 'raws')
makeGIF(pm.testing, lhs, 'sims')
makeGIF(pm.seg_images, lhs, 'segs')
makeGIF(pm.iou_images, lhs, 'iou')
makeGIF(pm.blend_images, lhs, 'blend')
