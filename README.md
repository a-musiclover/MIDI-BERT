# MidiBERT-Piano
<p align="center">
    <img src="resources/fig/midibert.png" width="800"/>
    <br>
    <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/github/license/wazenmai/MIDI-BERT?logoColor=blue" /></a>
    <a href="http://arxiv.org/licenses/nonexclusive-distrib/1.0/"><img alt="ARXIV LICENSE" src="https://img.shields.io/badge/License-arxiv-lightgrey" /> </a>
    <a href=""><img alt="STAR" src="https://img.shields.io/github/stars/wazenmai/MIDI-BERT"/> </a>
    <a href="https://github.com/wazenmai/MIDI-BERT/issues"><img alt="ISSUE" src="https://img.shields.io/github/issues/wazenmai/MIDI-BERT" /></a>

</p>
Authors: <a href="https://sophia1488.github.io">Yi-Hui (Sophia) Chou</a>, <a href="https://github.com/wazenmai">I-Chun (Bronwin) Chen</a>

## Introduction
This is the official repository for the paper, [MidiBERT-Piano: Large-scale Pre-training for Symbolic Music Understanding](https://arxiv.org/pdf/2107.05223.pdf).

With this repository, you can
* pre-train a MidiBERT-Piano with your customized pre-trained dataset
* fine-tune & evaluate on 4 downstream tasks
* extract melody (mid to mid) using pre-trained MidiBERT-Piano

All the datasets employed in this work are publicly available.


## Quick Start
### For programmers
If you'd like to reproduce the results (MidiBERT) shown in the paper, 
![image-20210710185007453](resources/fig/result.png)

1. Please download the [checkpoints](https://drive.google.com/drive/folders/1ceIfC1UugZQHPgpEEMkdAF0VhZ1EeLl3?usp=sharing), and rename files like the following

	(Note: we only provide checkpoints for models in CP representations)
```
MidiBERT/CP/
result
└── finetune
	└── melody_default
		└── model_best.ckpt
	└── velocity_default
		└── model_best.ckpt
	└── composer_default
		└── model_best.ckpt
	└── emotion_default
		└── model_best.ckpt
```

2. Please refer to [Readme]() in MidiBERT folder, 

 and you are free to go!  *(btw, no gpu is needed for evaluation)*

### For musicians who want to test melody extraction
Edit `scripts/melody_extraction.sh` and modify `song_path` to your midi path.
The midi file to predicted melody will be saved at the root folder.
```
./scripts/melody_extraction.sh
```
I've experimented this on Adele hello (piano cover), and I think it's good.  
But for non-pop music like Mozart sonata, I feel like the model is pretty confused.  This is expected.  As the training data is POP909 Dataset, the model knows very little about classical music.  

Side note: I try to make it more friendly for non-programmers.  Feel free to open an issue if there's any problem.

## Installation
* Python3
* Install generally used packages for MidiBERT-Piano:
```python
git clone https://github.com/wazenmai/MIDI-BERT.git
cd MIDI-BERT
pip install -r requirements.txt
```

## Usage
Please see `scripts` folder, which includes bash file for
* prepare data
* pretrain
* finetune
* eval
* melody extraction

You may need to change the folder/file name or any config settings you prefer.


## Repo Structure```
```
Data/
└── Dataset/       
    └── pop909/       
    └── .../
└── CP_data/
    └── pop909_train.npy
    └── *.npy

data_creation/
└── preprocess_pop909/
└── prepare_data/       # convert midi to CP_data 
    └── dict/           # CP dictionary 

melody_extraction/
└── skyline/
└── midibert/

MidiBERT/
└── *py

```

## More
For more details on data preparation, please go to `data_creation` and follow Readme.
## A. Prepare Data

All data in CP/REMI token are stored in ```data/CP``` & ```data/remi```, respectively, including the train, valid, test split.

You can also preprocess as below.

### 1. Download Dataset and Preprocess
Save the following dataset in `Dataset/`
* [Pop1K7](https://github.com/YatingMusic/compound-word-transformer)
* [ASAP](https://github.com/fosfrancesco/asap-dataset)
  * Download ASAP dataset from the link
* [POP909](https://github.com/music-x-lab/POP909-Dataset)
  * preprocess to have 865 pieces in qualified 4/4 time signature
  * ```cd preprocess_pop909```
  * ```exploratory.py``` to get pieces qualified in 4/4 time signature and save them at ```qual_pieces.pkl```
  * ```preprocess.py``` to realign and preprocess
  * Special thanks to Shih-Lun (Sean) Wu
* [Pianist8](https://zenodo.org/record/5089279)
  * Step 1: Download Pianist8 dataset from the link
  * Step 2: Run `python3 pianist8.py` to split data by `Dataset/pianist8_(mode).pkl`
* [EMOPIA](https://annahung31.github.io/EMOPIA/)
  * Step 1: Download Emopia dataset from the link
  * Step 2: Run `python3 emopia.py` to split data by `Dataset/emopia_(mode).pkl`

### 2. Prepare Dictionary

```dict/make_dict.py``` customize the events & words you'd like to add.

In this paper, we only use *Bar*, *Position*, *Pitch*, *Duration*.  And we provide our dictionaries in CP & REMI representation.

```dict/CP.pkl```

```dict/remi.pkl```

### 3. Prepare CP & REMI
Note that the CP & REMI tokens here only contain Bar, Position, Pitch, and Duration.
Please look into the repos below if you prefer the original definition of CP & REMI tokens.

```./prepare_data/CP```

* Run ```python3 main.py ```.  Please specify the dataset and whether you wanna prepare an answer array for the task (i.e. melody extraction, velocity prediction, composer classification and emotion classification).
* For example, ```python3 main.py --dataset=pop909 --task=melody --dir=[DIR_TO_STORE_DATA]```
* For custom dataset, run `python3 main.py --input_dir={your_input_directory}`, and the data in CP tokens will be saved at `../../data/CP/{your input directory name}.npy`.  Or you can specify the filename by adding `--name={filename}`.

```./prepare_data/remi/```

* The same logic applies to preparing REMI data. 

Acknowledgement: [CP repo](https://github.com/YatingMusic/compound-word-transformer), [remi repo](https://github.com/YatingMusic/remi/tree/6d407258fa5828600a5474354862353ef4e4e8ae)

## B. Pre-train a MidiBERT-Piano

```./MidiBERT/CP``` and ```./MidiBERT/remi```

* pre-train a MidiBERT-Piano
```python
python3 main.py --name=default
```
A folder named ```CP_result/pretrain/default/``` will be created, with checkpoint & log inside.

* customize your own pre-training dataset
Feel free to select given dataset and add your own dataset.  To do this, add ```--dataset```, and specify the respective path in ```load_data()``` function.
For example,
```python
# to pre-train a model with only 2 datasets
python3 main.py --name=default --dataset pop1k7 asap	
``` 

Acknowledgement: [HuggingFace](https://github.com/huggingface/transformers), [codertimo/BERT-pytorch](https://github.com/codertimo/BERT-pytorch)

Special thanks to Chin-Jui Chang

## C. Fine-tune & Evaluate on Downstream Tasks

```./MidiBERT/CP``` and ```./MidiBERT/remi```

### 1. Fine-tuning

* ```finetune.py```
```python
python3 finetune.py --task=melody --name=default
```
A folder named ```CP_result/finetune/{name}/``` will be created, with checkpoint & log inside.

### 2. Evaluation

* ```eval.py```
```python
python3 eval.py --task=melody --cpu --ckpt=[ckpt_path]
```
Test loss & accuracy will be printed, and a figure of confusion matrix will be saved.

*The same logic applies to REMI representation.*

## D. Baseline Model (Bi-LSTM)

```./baseline/CP``` & ```./baseline/remi```

We seperate our baseline model to note-level tasks, which used a Bi-LSTM, and sequence-level tasks, which used a Bi-LSTM + Self-attention model.

For evaluation, in note-level task, please specify the checkpoint name.
In sequence-level task, please specify only the output name you set when you trained.

* Train a Bi-LSTM
	* note-level task
	```python
	python3 main.py --task=melody --name=0710
	```
	* sequence-level task
	```python
	python3 main.py --task=composer --output=0710
	```

* Evaluate
	* note-level task:
	```python
	python3 eval.py --task=melody --ckpt=result/melody-LSTM/0710/LSTM-melody-classification.pth
	```
	* sequence-level task
	```python
	python3 eval.py --task='composer' --ckpt=0710
	```

The same logic applies to REMI representation. 

Special thanks to Ching-Yu (Sunny) Chiu

## E. Skyline

Get the accuracy on pop909 using skyline algorithm
```python
python3 cal_acc.py
```

Since Pop909 contains *melody*, *bridge*, *accompaniment*, yet skyline cannot distinguish  between melody and bridge.

There are 2 ways to report its accuracy:

1. Consider *Bridge* as *Accompaniment*, attains 78.54% accuracy
2. Consider *Bridge* as *Melody*, attains 79.51%

Special thanks to Wen-Yi Hsiao for providing the code for skyline algorithm.

## Citation

If you find this useful, please cite our paper.

```
@article{midibertpiano,
  title={{MidiBERT-Piano}: Large-scale Pre-training for Symbolic Music Understanding},
  author={Yi-Hui Chou and I-Chun Chen and Chin-Jui Chang and Joann Ching, and Yi-Hsuan Yang},
  journal={arXiv preprint arXiv:2107.05223},
  year={2021}
}
```

