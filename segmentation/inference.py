import os

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch
from torchvision import transforms

from .data import get_preprocessing


class Evaluator():
    def __init__(self, model_path):
        super().__init__()

        # setup image processing functions
        encoder_weights = 'imagenet'
        encoder = os.path.basename(model_path).split('-')[1]
        self.preprocessing_fn = smp.encoders.get_preprocessing_fn(encoder, encoder_weights)
        self.to_PIL = transforms.ToPILImage()

        # define metrics
        self.loss = smp.utils.losses.DiceLoss()
        self.metric = smp.utils.metrics.IoU(threshold=0.5)

        # load best saved checkpoint
        self.model = torch.jit.load(model_path)
        self.model.eval()

    def evaluate(self, image_path, mask_path, result_path):
        # read data
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)

        # extract alpha channel
        _, _, _, mask = cv2.split(mask)
        masks = [(mask != 0)]
        mask = np.stack(masks, axis=-1).astype('float')

        # apply preprocessing
        preprocessing = get_preprocessing(self.preprocessing_fn)
        sample = preprocessing(image=image, mask=mask)
        image, mask = sample['image'], sample['mask']

        # to tensor and fake a batch
        image = torch.from_numpy(image).unsqueeze(0)
        mask = torch.from_numpy(mask).unsqueeze(0)

        with torch.no_grad():
            prediction = self.model(image)

            loss_value = self.loss(prediction, mask).numpy()
            metric_value = self.metric(prediction, mask).numpy()

            self.to_PIL(prediction.squeeze(0)).save(result_path)

        return loss_value, metric_value


def trace_model(model_path):
    model = torch.load(model_path)
    model.cpu()

    traced_model = torch.jit.trace(model, torch.randn(1, 3, 384, 480))  # with fake input
    torch.jit.save(traced_model, f'{os.path.splitext(model_path)[0]}-traced.pth')


if __name__ == '__main__':
    pass
    # evaluator = Evaluator(model_path)
    # evaluator.evaluate(image_path, mask_path, result_path)
