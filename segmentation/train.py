import os
import sys
from argparse import ArgumentParser
from datetime import datetime

import segmentation_models_pytorch as smp
import torch
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from data import PrinterDataset, get_preprocessing


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('data_dir', type=str)
    parser.add_argument('--checkpoints_dir', type=str, default='./checkpoints')
    parser.add_argument('--architecture', type=str, default='FPN')
    parser.add_argument('--encoder', type=str, default='se_resnet50')
    parser.add_argument('--encoder_weights', type=str, default='imagenet')
    parser.add_argument('--activation', type=str, default='sigmoid')
    parser.add_argument('--augmentation', action='store_false')
    return vars(parser.parse_args())


def train(data_dir, checkpoints_dir, architecture, encoder, encoder_weights, activation, augmentation):
    if not os.path.exists(data_dir):
        print('No Data!')
        sys.exit(-1)

    os.makedirs(checkpoints_dir, exist_ok=True)

    experiment_name = f'{architecture}-{encoder}{"-aug" if augmentation else ""}'
    writer = SummaryWriter(os.path.join('runs', f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}-{experiment_name}'))

    device = torch.device('cuda')

    # create segmentation model with pretrained encoder
    architecture_fn = getattr(smp, architecture)
    model = architecture_fn(encoder_name=encoder, encoder_weights=encoder_weights, classes=1, activation=activation)
    # get preprocess function for pretrained model
    preprocessing_fn = smp.encoders.get_preprocessing_fn(encoder, encoder_weights)

    # create dataset
    train_dataset = PrinterDataset(data_dir, preprocessing=get_preprocessing(preprocessing_fn, apply_augmentation=augmentation))
    valid_dataset = PrinterDataset(data_dir, preprocessing=get_preprocessing(preprocessing_fn), is_valid=True)
    # setup dataloader
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, num_workers=12)
    valid_loader = DataLoader(valid_dataset, batch_size=1, shuffle=False, num_workers=4)

    # loss and metrics
    loss = smp.utils.losses.DiceLoss()
    metrics = [smp.utils.metrics.IoU(threshold=0.5)]
    optimizer = torch.optim.Adam([dict(params=model.parameters(), lr=0.0001)])

    # create epoch runners
    train_epoch = smp.utils.train.TrainEpoch(model, loss=loss, metrics=metrics, optimizer=optimizer, device=device, verbose=True)
    valid_epoch = smp.utils.train.ValidEpoch(model, loss=loss, metrics=metrics, device=device, verbose=True)

    # train model for 40 epochs
    max_score = 0
    for step in range(0, 30):
        print(f'\nEpoch {step + 1}:')
        train_logs = train_epoch.run(train_loader)
        valid_logs = valid_epoch.run(valid_loader)

        # write tensorboard
        writer.add_scalar('Loss/train', train_logs['dice_loss'], step)
        writer.add_scalar('Loss/valid', valid_logs['dice_loss'], step)
        writer.add_scalar('IoU/train', train_logs['iou_score'], step)
        writer.add_scalar('IoU/valid', valid_logs['iou_score'], step)
        writer.flush()

        # do something (save model, change lr, etc.)
        if max_score < valid_logs['iou_score']:
            max_score = valid_logs['iou_score']
            torch.save(model, os.path.join(checkpoints_dir, f'{experiment_name}-best_model.pth'))
            print('Model saved!')

        if step == 20:
            optimizer.param_groups[0]['lr'] = 1e-5
            print('Decrease decoder learning rate to 1e-5!')

    writer.close()


if __name__ == '__main__':
    train(**parse_args())
