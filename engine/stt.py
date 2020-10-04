#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: stt.py [-h] [--config CONFIG]
# 
# Speech-To-Text engine using CMUSphinx and PocketSphinx
# When a hotword is detected, it starts to transcribe text
# 
# optional arguments:
#   -h, --help       show this help message and exit
#   --config CONFIG  Path to jarvis configuration file


## input: jarvis/hotword -> detected
## raw_input: jarvis/internal/mic_buffer_stream -> raw bytes mic buffer stream
## output: jarvis/stt -> (started|stopped|error|command:[words])


## import global packages
import os, sys, time, traceback, base64, argparse, configparser, re
import lib.helper as helper
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *


## TODO: obsolete?
## 		 might be, but it's implementing the official API of mqtt:jarvis/hotword
## this function is being called when hotword.py sends a message
def hotword_callback(client, userdata, message):
	global record_phrases
	# decode the message
	message.payload = message.payload.decode()
	# if the hotword got detected, start recording audio
	if message.payload == "detected":
		record_phrases = True


# this function is being called when hotword.py send the raw mic data
def mic_buffer_callback(client, userdata, message):
	global decoder, utt_started
	try:
		# if hotword.py sends "end", stop the recording, process the chunks and publish the result
		if message.payload.decode() == "end":
			# end recording
			decoder.end_utt()
			helper.log("stt", "stopping utterance")
			utt_started = False
			# process chunks, publishes the result
			process_stt()
		# if hotword.py sends binary data, feed the stt with the raw chunks
		else:
			# if the engine is still inactive, start it
			if not utt_started:
				# start the engine
				decoder.start_utt()
				helper.log("stt", "starting utterance")
				utt_started = True
			# decode the chunk
			chunk = base64.b64decode(message.payload.decode())
			# feed stt with the chunk
			decoder.process_raw(chunk[1::4], False, False)
	except Exception:
		print("-> exception")
		traceback.print_exc()


# this function processes the chunks after jarvis/internal/mic_buffer_stream returns "end"
def process_stt():
	global decoder
	# get the raw hypothesis (including html tags for silence, etc...)
	hypothesis_raw = " ".join([seg.word.lower() for seg in decoder.seg()])
	# strip off the tags and only get the lowercase text
	hypothesis = clean_tags(hypothesis_raw).strip()
	# print the hypothesis
	print("-> best hypothesis: {}".format(hypothesis_raw))
	# publish the hypothesis
	mqtt.publish("jarvis/stt", "command:" + hypothesis)


# this functions strips off html tags from a string
def clean_tags(raw_txt):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr, '', raw_txt)
	return cleantext


# add a description and parse arguments
parser = argparse.ArgumentParser(description="Speech-To-Text engine using CMUSphinx and PocketSphinx\nWhen a hotword is detected, it starts to transcribe text", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()


# get the config file from argparse and read it
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(args.config)
config = config["stt"]


# initialize a mqtt client that listens to the jarvis/hotword channel
mqtt = helper.MQTT(client_id="stt.py")
mqtt.on_message(hotword_callback)
mqtt.subscribe("jarvis/hotword")


# initialize another mqtt client that listens to the raw mic stream
mqtt2 = helper.MQTT(client_id="stt.py:mic_buffer")
mqtt2.on_message(mic_buffer_callback)
mqtt2.subscribe("jarvis/internal/mic_buffer_stream")


# initialize the pocketsphinx decoder
decoder_config = Decoder.default_config()
decoder_config.set_string('-hmm', config["acoustic_model"])
decoder_config.set_string('-lm', config["language_model"])
decoder_config.set_string('-dict', config["dictionary"])
decoder_config.set_string('-rawlogdir', config["logdir"])
decoder = Decoder(decoder_config)
utt_started = False


# tell everyone that the decoder is working and ready to process data
helper.log("stt", "starting pocketsphinx passively")
mqtt.publish("jarvis/stt", "started")


# mainloop
try:
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	mqtt.publish("jarvis/stt", "stopped")
	exit(0)

mqtt.publish("jarvis/stt", "stopped")