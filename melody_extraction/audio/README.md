# Melody Extraction on POP909 and Pianist8

We have runned melody extraction algorithms on random selected songs in POP909 and Pianist8. The algorithms are listed below:
- skyline
- A Convolutional Approach to Melody Line Identification in Symbolic Scores (https://arxiv.org/abs/1906.10547) (https://github.com/sophia1488/symbolic-melody-identification), we train the model on POP909 train split.
- MidiBERT finetuned with POP909 for melody extraction, here we view POP909's "melody" and "bridge" as melody, the detailed information of these categorization please see https://github.com/music-x-lab/POP909-Dataset/tree/master.

## :headphones: 2024/04 Update 
Upload corresponding MP3 files in directories with postfix `_mp3`.
Since the files are too large, please access with this link: https://drive.google.com/file/d/1cRcTAV43n-1VeJciCxQXSx5TLyChOXHI/view


## In-domain Dataset - POP909
- 018.mid
- 067.mid
- 395.mid
- 596.mid
- 828.mid

|| Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
|Skyline | 79.52 | 81.42 | 56.57 | 66.76 |
|CNN | 92.08 | 88.95 | 89.3 | 89.13 |
|MidiBERT | 99.06 | 98.68 | 98.72 | 98.7 |

## Out-domain Dataset - Pianist8
- Clayderman_I_Have_A_dream
- Clayderman_I_Like_Chopin
- Clayderman_Yesterday_Once_More
- Yiruma_Love_Hurts
- Yiruma_River_Flows_In_You

## Filename Description
- `_gt`: ground truth
- `_skyline`: melody extracted by skyline algorithm
- `_cnn`: melody extracted by A Convolutional Approach to Melody Line Identification in Symbolic Scores
- `_ours`: melody extracted by MidiBERT
