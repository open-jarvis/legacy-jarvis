#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import engine.lib.helper as helper

import os
from pocketsphinx import LiveSpeech, get_model_path

model_path = get_model_path()

speech = LiveSpeech(
	verbose=True,
	sampling_rate=16000,
	buffer_size=2048,
	no_search=False,
	full_utt=False,
	hmm="/home/pi/jarvis/resources/stt/acoustic_model/",
	lm="/home/pi/jarvis/resources/stt/german.lm.bin",
	dic="/home/pi/jarvis/resources/stt/german.dict"
)

for phrase in speech:
	print(phrase)
