# -*- coding: utf-8 -*-
"""
Created on Dec 14 2020

@author: Yi-Hui (Sophia) Chou 
"""
import os
from model_lstm import LSTM_Net 
from model_finetune import LSTM_Finetune
from pop_dataset import PopDataset
from torch.utils.data import DataLoader
import tqdm
import torch
import torch.nn as nn
from pathlib import Path
import json
import utils_bestloss as utils
import time
from train import training, valid
import numpy as np
import argparse
import pickle


def get_args():
    parser = argparse.ArgumentParser(description='Argument Parser for downstream classification')
    ### mode ###
    parser.add_argument('-t', '--task', choices=['melody', 'velocity'], required=True)
    parser.add_argument('--finetune', action="store_true")  # default: false

    ### path setup ### 
    parser.add_argument('--input', type=str, default='/home/yh1488/NAS-189/home/CP_data/POP909cp.npy',help='Path to input numpy file for pop909 dataset')
    parser.add_argument('--answer', type=str, help='Path to answer numpy file for pop909 dataset')
    parser.add_argument('--dict', type=str, default='../remi/my-checkpoint/CP.pkl')
    
    ### parameter setting ###
    parser.add_argument('--layer', type=str, default='12', help='specify embedding layer index')
    parser.add_argument('--class-num', type=int)
    parser.add_argument('--hs', type=int, default=256)
    parser.add_argument('--train-batch', default=16, type=int)
    parser.add_argument('--dev-batch', default=8, type=int)
    parser.add_argument('--name', type=str, help='Used for output directory name', required=True)
    parser.add_argument('--cuda', default=0, type=int, help='Specify cuda number')
    parser.add_argument('--gain', type=float, default=2.5)
    parser.add_argument('--lr', type=float, default=1e-3)

    args = parser.parse_args()
    
    if args.task == 'melody':
        args.answer ='/home/yh1488/NAS-189/home/CP_data/POP909cp_melans.npy'
        args.class_num = 3
    elif args.task == 'velocity':
        args.answer ='/home/yh1488/NAS-189/home/CP_data/POP909cp_velans.npy'
        args.class_num = 6 
    
    return args


def load_ft_data(layer, task):
    task_name = 'melody identification' if task == 'melody' else 'velocity classification'
    print("\nloading data for fine-tuning {} ...".format(task_name))
    print("Using embedding layer {}".format(layer))
    X_train = np.load('/home/yh1488/NAS-189/home/BERT/cp_embed/POPtrain_' + layer + '.npy')
    X_val = np.load('/home/yh1488/NAS-189/home/BERT/cp_embed/POPvalid_' + layer + '.npy')

    return X_train, X_val

def load_data(data, task):
    task_name = 'melody identification' if task == 'melody' else 'velocity classification'
    print("\nloading data for {} ...".format(task_name))
    all = np.load(data)
    X_train, X_val, _ = np.split(all, [int(.8 * len(all)), int(.9 * len(all))])
    
    return X_train, X_val


def main():
    args = get_args()
    cuda_num = args.cuda 
    cuda_str = 'cuda:'+str(cuda_num)
    device = torch.device(cuda_str if torch.cuda.is_available() else 'cpu')
    print(device)

    exp_name = '-finetune' if args.finetune else '-LSTM'
    exp_dir = os.path.join('result', args.task + exp_name, args.name)
    target_jsonpath = exp_dir
    
    if not os.path.exists(exp_dir):
        Path(exp_dir).mkdir(parents = True, exist_ok = True)

    train_epochs = 1000
    lr = args.lr 
    patience = 20
    
    print("loading dictionary...")
    with open(args.dict, 'rb') as f:
        e2w, w2e = pickle.load(f)

    # prepare data to 80:10:10
    if args.finetune:
        X_train, X_val = load_ft_data(args.layer, args.task)
    else:
        X_train, X_val = load_data(args.input, args.task)
    
    all_ans = np.load(args.answer)
    y_train, y_val, _ = np.split(all_ans, [int(.8 * len(all_ans)), int(.9 * len(all_ans))])
    
    trainset = PopDataset(X=X_train, y=y_train)
    validset = PopDataset(X=X_val, y=y_val) 
    train_loader = DataLoader(trainset, batch_size = args.train_batch, shuffle = True)
    print("   len of train_loader", len(train_loader))
    valid_loader = DataLoader(validset, batch_size = args.dev_batch, shuffle = True)
    print("   len of valid_loader", len(valid_loader))
    
    print("\ninitializing model...")    
    if args.finetune:
        model = LSTM_Finetune(class_num=args.class_num, hidden_size=args.hs)
    else:
        model = LSTM_Net(e2w=e2w, class_num=args.class_num)
    
    #for name, param in model.named_parameters():
        # nn.init.constant(param, 0.0)
    #    if 'weight' in name and args.task == 'velocity':
    #        torch.nn.init.xavier_uniform_(param, gain=args.gain)

    model.cuda(cuda_num)

    optimizer = torch.optim.SGD(
            model.parameters(),
            lr = lr,
            momentum=0.9
        )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            factor=0.3, # follow openunmix
            patience=80,
            cooldown=10
        )

    es = utils.EarlyStopping(patience= patience)
    
    t = tqdm.trange(1, train_epochs +1, disable = False)
    train_losses, train_accs = [], []
    valid_losses, valid_accs = [], []
    train_times = []
    best_epoch = 0
    stop_t = 0
    print("   start training...")

    for epoch in t:
#        break
        t.set_description("Training Epoch")
        end = time.time()
        train_loss, train_acc = training(model, device, train_loader, optimizer, args.finetune)
        valid_loss, valid_acc = valid(model, device, valid_loader, args.finetune)
        
        scheduler.step(valid_loss)
        train_losses.append(train_loss.item())
        valid_losses.append(valid_loss.item())
        train_accs.append(train_acc.item())
        valid_accs.append(valid_acc.item())

        t.set_postfix(
        train_loss=train_loss.item(), val_loss=valid_loss.item()
        )

        stop = es.step(valid_loss.item())

        if valid_loss.item() == es.best:
            best_epoch = epoch
            
        utils.save_checkpoint({
                    'epoch': epoch + 1,
                    'state_dict': model.state_dict(),
                    'best_loss': es.best,
                    'optimizer': optimizer.state_dict(),
                    'scheduler': scheduler.state_dict()
                },
                is_best=valid_loss == es.best,
                path=exp_dir,
                target='LSTM-'+args.task+'-classification'
            )

            # save params
        params = {
                'epochs_trained': epoch,
#                'args': vars(args),
                'best_loss': es.best,
                'best_epoch': best_epoch,
                'train_loss_history': train_losses,
                'valid_loss_history': valid_losses,
                'train_acc_history': train_accs,
                'valid_acc_history': valid_accs,
                'train_time_history': train_times,
                'num_bad_epochs': es.num_bad_epochs,
    #            'commit': commit
            }

        with open(os.path.join(target_jsonpath,  'LSTM-' + args.task + '.json'), 'w') as outfile:
            outfile.write(json.dumps(params, indent=4, sort_keys=True))

        train_times.append(time.time() - end)
        
        if stop:
                print("Apply Early Stopping and retrain")
#                break
                stop_t +=1
                if stop_t >=5:
                    break
                lr = lr*0.2
                optimizer = torch.optim.SGD(
                    model.parameters(),
                    lr=lr,
                    momentum=0.9
                )

                scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                        optimizer,
                        factor=0.3, # follow openunmix
                        patience=80,
                        cooldown=10
                    )

                es = utils.EarlyStopping(patience= patience, best_loss = es.best)
    

if __name__ == "__main__":
    main()