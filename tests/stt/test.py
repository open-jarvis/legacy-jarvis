#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## stt.py - listenes for the hotword and sends a mqtt message
## stt.py uses https://cmusphinx.github.io/

## input: jarvis/hotword -> detected
## raw_inpput: jarvis/internal/mic_buffer_stream -> raw bytes mic buffer stream
## output: jarvis/stt -> (command:[words]|started|stopped|error)


import os, sys, time, traceback, base64
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

config = Decoder.default_config()
# config.set_string('-hmm', "/home/pi/jarvis/resources/stt/v2/acoustic_model/")
# config.set_string('-lm', "/home/pi/jarvis/resources/stt/v2/de.cmd.lm")
# config.set_string('-dict', "/home/pi/jarvis/resources/stt/v2/de.cmd.dict")
config.set_string('-hmm', "/home/pi/jarvis/resources/stt/v1/acoustic_model/")
config.set_string('-lm', "/home/pi/jarvis/resources/stt/v1/german.lm.bin")
config.set_string('-dict', "/home/pi/jarvis/resources/stt/v1/german.dict")
decoder = Decoder(config)

rootdir = "files/"

output_str = "\n\n=====================\n"

for subdir, dirs, files in os.walk(rootdir):
	for filepath in files:
		print("reading file '{}'".format(filepath))
		buf = bytearray(160)  # change the buffer size doesn't make a change...
		# buf = bytearray(1024)
		with open("{}{}".format(rootdir, filepath), 'rb') as f:
			decoder.start_utt()
			while f.readinto(buf):
				decoder.process_raw(buf, False, False)
			decoder.end_utt()
		
		result = [seg.word for seg in decoder.seg()]
		target = filepath.split(".")[0].replace("-",  " ").replace(" silenced", "").replace("1", "").replace("2", "").replace("3", "")
		target_ = target.upper().split(" ")

		output_str += "           File : {}\n".format(filepath)
		output_str += "Best hypothesis : {}\n".format(", ".join(result))
		output_str += "      Should be : {}\n".format(target)
		output_str += "=====================\n"

print(output_str)
