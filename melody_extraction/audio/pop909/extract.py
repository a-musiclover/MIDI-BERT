"""
Extract Ground Truth from POP909 songs
"""

import os
import sys
import numpy as np
import miditoolkit

files = []
for f in os.listdir(sys.argv[1]):
    if f.endswith('.mid'):
        files.append(f)

for f in files:
    midi = miditoolkit.midi.parser.MidiFile(os.path.join(sys.argv[1], f))
    midi.instruments = midi.instruments[:2]
    num = f.split(".")[0]
    midi.dump(os.path.join(sys.argv[2], num + "_gt.mid"))
