import os

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch
from torchvision import transforms
from PIL import Image

import sys
sys.path.append('segmentation')
from data import get_preprocessing


class Evaluator():
    def __init__(self, model_path, threshold=0.5):
        super().__init__()

        self.threshold = threshold

        # setup image processing functions
        encoder_weights = 'imagenet'
        encoder = os.path.basename(model_path).split('-')[1]
        self.preprocessing_fn = smp.encoders.get_preprocessing_fn(encoder, encoder_weights)
        self.to_PIL = transforms.ToPILImage()

        # define metrics
        self.loss = smp.utils.losses.DiceLoss()
        self.metric = smp.utils.metrics.IoU(threshold=self.threshold)

        # load best saved checkpoint
        self.model = torch.jit.load(model_path)
        self.model.eval()

    def evaluate(self, image_path, mask_path, prediction_path=None, iou_image_path=None, blend_image_path=None):
        # read data
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)

        # extract alpha channel
        _, _, _, mask = cv2.split(mask)
        masks = [(mask != 0)]
        mask = np.stack(masks, axis=-1).astype('float')

        # keep origin image for later use
        origin_image = Image.fromarray(image)
        origin_image = origin_image.resize((480, 384))

        # apply preprocessing
        preprocessing = get_preprocessing(self.preprocessing_fn)
        sample = preprocessing(image=image, mask=mask)
        image, mask = sample['image'], sample['mask']

        # to tensor and fake a batch
        image = torch.from_numpy(image).unsqueeze(0)
        mask = torch.from_numpy(mask).unsqueeze(0)

        with torch.no_grad():
            # get model interence
            prediction = self.model(image)

            # calculate the metrics
            loss_value = self.loss(prediction, mask).numpy()
            metric_value = self.metric(prediction, mask).numpy()

            # get IoU image and union mask
            prediction = (prediction > self.threshold).type(prediction.dtype)
            prediction = prediction.squeeze(0)
            mask = mask.squeeze(0)
            iou_image = torch.cat([prediction, mask, torch.zeros_like(prediction)])
            union_mask = torch.logical_or(prediction, mask).double()

            # blend image
            iou_image = self.to_PIL(iou_image)
            union_mask = self.to_PIL(union_mask)
            blend_image = Image.blend(origin_image, iou_image, 0.35)
            blend_image = Image.composite(blend_image, origin_image, union_mask)

            # save results
            if prediction_path is not None:
                self.to_PIL(prediction).save(prediction_path)
            if iou_image_path is not None:
                iou_image.save(iou_image_path)
            if blend_image_path is not None:
                blend_image.save(blend_image_path)

        return loss_value, metric_value


def trace_model(model_path):
    model = torch.load(model_path)
    model.cpu()

    traced_model = torch.jit.trace(model, torch.randn(1, 3, 384, 480))  # with fake input
    torch.jit.save(traced_model, f'{os.path.splitext(model_path)[0]}-traced.pth')


if __name__ == '__main__':
    pass
    # evaluator = Evaluator(model_path)
    # evaluator.evaluate(image_path, mask_path, prediction_path, iou_image_path, blend_image_path)
