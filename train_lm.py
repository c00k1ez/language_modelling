import torch
import torch.nn as nn

import pytorch_lightning as pl 

from utils import load_dataloaders, seed_all, CustomModelCheckpoint
from framework.models import ClassicLanguageModel, AttentionLanguageModel
from framework.lm_framework import LMFramework

from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.logging import CometLogger

import os
import confuse

import nltk
import argparse


if __name__ == "__main__":

    nltk.download('punkt')

    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, default='./configs/lm_base_config.yaml')
    parser.add_argument('--model', type=str, default='classic_lm')
    parser.add_argument('--experiment_name', type=str, default='experiment_1')
    parser.add_argument('--api_key',type=str, default='')
    args = parser.parse_args()

    # load config file
    config = confuse.Configuration('research')
    config.set_file(args.config_file)

    # set model
    model = None
    if args.model == 'classic_lm':
        model = ClassicLanguageModel(**config['model'].get(), model_name=args.model)
    elif args.model == 'attention_lm':
        model = AttentionLanguageModel(**config['model'].get(), model_name=args.model)
    else:
        raise ValueError("You have wrong --model parameter")
    
    # seed everything
    seed_all(config['general']['seed'].get())

    # get dataloaders and training framework
    loaders = load_dataloaders(**config['dataloaders'].get())
    framework = LMFramework(model, **config['optimizer'].get(), loaders=loaders)

    if not os.path.isdir(config['general']['checkpoint_path'].get()):
        os.makedirs(config['general']['checkpoint_path'].get())
    
    if not os.path.isdir(config['trainer_params']['default_save_path'].get()):
        os.makedirs(config['trainer_params']['default_save_path'].get())

    exp_name =  args.experiment_name + \
                '_' + \
                args.model + \
                '_' + \
                config['dataloaders']['tokenizer_type'].get() + \
                '_epochs_' + \
                str(config['trainer_params']['max_epochs'].get())
    
    print("starting " + exp_name + " experiment")

    # setup logger
    api_key = args.api_key
    if api_key == '':
        api_key = os.environ['API_KEY']
    logger = CometLogger(
        api_key=os.environ['API_KEY'],
        workspace="c00k1ez",
        project_name="low-resource-lm-research",
        experiment_name=exp_name
    )

    # get all config data to send in to comet.ml
    config_data = {}
    cfg_raw = config.get()
    for key in cfg_raw.keys():
        config_data.update(dict(cfg_raw[key]))
    logger.experiment.log_parameters(config_data)

    model_name = args.model + '_' + config['dataloaders']['tokenizer_type'].get()
    
    # setup my custom checkpoint callback
    checkpoint_callback = CustomModelCheckpoint(
        model_name=model_name, 
        filepath=config['general']['checkpoint_path'].get(),
        save_top_k=1,
        verbose=True,
        monitor='val_loss',
        mode='min',
        prefix=args.model + '_'
    )

    trainer = pl.Trainer(**config['trainer_params'].get(),
                        checkpoint_callback=checkpoint_callback,
                        print_nan_grads=True,
                        profiler=True,
                        logger=logger
                        )
    trainer.fit(framework)


    