import csv
import os
from glob import glob

import albumentations as A
import cv2
import numpy as np
from torch.utils.data import Dataset


class PrinterDataset(Dataset):
    """Printer Dataset. Read images, apply augmentation and preprocessing transformations.

    Args:
        data_dir (str): path to data folder
        preprocessing (albumentations.Compose): data preprocessing (e.g. normalization, shape manipulation, etc.)
        is_valid (boolean): whether the dataset is for validation or not
    """

    def __init__(self, data_dir, preprocessing=None, is_valid=False):
        self.images_fps = []
        self.masks_fps = []

        jobs = glob(os.path.join(data_dir, 'UMval' if is_valid else 'UMtrain', 'UM*'))
        for j in jobs:
            if not os.path.isdir(j):
                continue
            images_dir = os.path.join(j, 'images')
            masks_dir = os.path.join(j, 'simulation', 'testing')
            if not os.path.exists(masks_dir):
                continue

            with open(os.path.join(j, 'test_list.txt')) as csvfile:
                filelist = csv.reader(csvfile, delimiter=',')
                for m, i in filelist:
                    self.images_fps.append(os.path.join(images_dir, f'{i.strip()}.png'))
                    self.masks_fps.append(os.path.join(masks_dir, f'{m.strip()}.png'))

        self.preprocessing = preprocessing

    def __getitem__(self, index):
        # read data
        image = cv2.imread(self.images_fps[index])
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(self.masks_fps[index], cv2.IMREAD_UNCHANGED)

        # extract alpha channel
        _, _, _, mask = cv2.split(mask)
        masks = [(mask != 0)]
        mask = np.stack(masks, axis=-1).astype('float')

        # apply preprocessing
        if self.preprocessing:
            sample = self.preprocessing(image=image, mask=mask)
            image, mask = sample['image'], sample['mask']

        return image, mask

    def __len__(self):
        return len(self.masks_fps)


def to_CHW(x, **kwargs):
    return x.transpose(2, 0, 1).astype('float32')


def get_preprocessing(preprocessing_fn, apply_augmentation=False):
    """Construct preprocessing transform

    Args:
        preprocessing_fn (callable): data normalization function (can be specific for each pretrained neural network)
        apply_augmentation (boolean): apply data augmentation or not
    Return:
        transform: albumentations.Compose
    """

    _transform = [A.Resize(384, 480)]

    if apply_augmentation:
        _transform += [
            A.HorizontalFlip(p=0.5),
            A.ShiftScaleRotate(scale_limit=0.5, rotate_limit=0, shift_limit=0.1, p=1, border_mode=0),
            A.IAAAdditiveGaussianNoise(p=0.2),
            A.IAAPerspective(p=0.5),
            A.OneOf([A.CLAHE(p=1), A.RandomBrightness(p=1), A.RandomGamma(p=1)], p=0.9),
            A.OneOf([A.IAASharpen(p=1), A.Blur(blur_limit=3, p=1), A.MotionBlur(blur_limit=3, p=1)], p=0.9),
            A.OneOf([A.RandomContrast(p=1), A.HueSaturationValue(p=1)], p=0.9)
        ]

    _transform += [
        A.Lambda(image=preprocessing_fn),
        A.Lambda(image=to_CHW, mask=to_CHW)
    ]

    return A.Compose(_transform)
