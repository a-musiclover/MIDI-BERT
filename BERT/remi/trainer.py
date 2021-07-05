import torch
import torch.nn as nn
from transformers import AdamW
from torch.nn.utils import clip_grad_norm_

import shutil
import numpy as np
import copy
import random
import tqdm
import sys

from model import MidiBert
from modelLM import MidiBertLM


class BERTTrainer:
    def __init__(self, midibert: MidiBert, train_dataloader, valid_dataloader, 
                lr, batch, max_seq_len, mask_percent, 
                with_cuda: bool=True, cuda_devices=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else 'cpu')
        self.midibert = midibert        # save this for ckpt
        self.model = MidiBertLM(midibert).to(self.device)
    
        if torch.cuda.device_count() > 1:
            print("Use %d GPUS" % torch.cuda.device_count())
            self.model = nn.DataParallel(self.model, device_ids=cuda_devices)

        self.train_data = train_dataloader
        self.valid_data = valid_dataloader
        
        self.optim = AdamW(self.model.parameters(), lr=lr, weight_decay=0.01)
        self.batch = batch
        self.max_seq_len = max_seq_len
        self.mask_percent = mask_percent
        self.Lseq = [i for i in range(self.max_seq_len)]

        self.loss_func = nn.CrossEntropyLoss(reduction='none')
    
    def compute_loss(self, predict, target, loss_mask):
        loss = self.loss_func(predict, target)
        loss = loss * loss_mask
        loss = torch.sum(loss) / torch.sum(loss_mask)
        return loss

    def get_mask_ind(self):
        mask_ind = random.sample(self.Lseq, round(self.max_seq_len * self.mask_percent))
        mask80 = random.sample(mask_ind, round(len(mask_ind)*0.8))
        left = list(set(mask_ind)-set(mask80))
        rand10 = random.sample(left, round(len(mask_ind)*0.1))
        cur10 = list(set(left)-set(rand10))
        return mask80, rand10, cur10


    def train(self):
        self.model.train()
        train_loss, train_acc = self.iteration(self.train_data, self.max_seq_len)
        return train_loss, train_acc

    def valid(self):
        self.model.eval()
        valid_loss, valid_acc = self.iteration(self.valid_data, self.max_seq_len, train=False)
        return valid_loss, valid_acc

    def iteration(self, training_data, max_seq_len, train=True):
        pbar = tqdm.tqdm(training_data, disable=False)

        total_acc, total_loss = 0, 0
        
        for ori_seq_batch in pbar:
            batch = ori_seq_batch.shape[0]
            ori_seq_batch = ori_seq_batch.to(self.device)       # [16, 512]
            input_ids = copy.deepcopy(ori_seq_batch)
            loss_mask = torch.zeros(batch, max_seq_len)
            
            for b in range(batch):
                # get index for masking
                mask80, rand10, cur10 = self.get_mask_ind()
                # apply mask, random, remain current token
                for i in mask80:
                    input_ids[b][i] = self.midibert.mask_word 
                    loss_mask[b][i] = 1 
                for i in rand10:
                    input_ids[b][i] = random.choice(range(len(self.midibert.e2w)))
                    loss_mask[b][i] = 1 
                for i in cur10:
                    loss_mask[b][i] = 1 
            
            loss_mask = loss_mask.to(self.device) #to(device).long()     # (4,512)

            # avoid attend to pad word
            attn_mask = (ori_seq_batch != self.midibert.pad_word).float().to(self.device)   # (4,512)

            y = self.model.forward(input_ids, attn_mask)

            # get the most likely choice with max
            output = np.argmax(y.cpu().detach().numpy(), axis=-1)
            output = output.astype(float)
            output = torch.from_numpy(output).to(self.device) #to(device).long()   # (4,512)

            # accuracy
            acc = torch.sum((ori_seq_batch == output).float() * loss_mask)
            acc /= torch.sum(loss_mask)
            total_acc += acc.item()

            # reshape (b, s, f) -> (b, f, s)
            y = y[:, ...].permute(0, 2, 1)

            # calculate losses
            loss = self.compute_loss(y, ori_seq_batch, loss_mask)

            # udpate only in train
            if train:
                self.model.zero_grad()
                loss.backward()
                clip_grad_norm_(self.model.parameters(), 3.0)
                self.optim.step()

            # acc
            sys.stdout.write('Loss: {:06f} | acc: {:06f} \r'.format(
                loss, acc)) 
                #train_iter, num_batches, total_loss, losses[0], losses[1], losses[2], losses[3], accs[0], accs[1], accs[2], accs[3]))

            total_loss += loss.item()
        
        return round(total_loss/len(training_data),4), round(total_acc/len(training_data),4)

    def save_checkpoint(self, epoch, train_acc, valid_acc, 
                        valid_loss, train_loss, is_best, filename):
        state = {
            'epoch': epoch + 1,
            'state_dict': self.midibert.state_dict(),
            'train_acc': train_acc,
            'valid_acc': valid_acc,
            'valid_loss': valid_loss,
            'train_loss': train_loss,
            'optimizer' : self.optim.state_dict()
        }

        torch.save(state, filename)

        best_mdl = filename.split('.')[0]+'_best.ckpt'
        if is_best:
            shutil.copyfile(filename, best_mdl)
