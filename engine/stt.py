#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## stt.py - listenes for the hotword and sends a mqtt message
## stt.py uses https://cmusphinx.github.io/

## input: jarvis/hotword -> detected
## raw_input: jarvis/internal/mic_buffer_stream -> raw bytes mic buffer stream
## output: jarvis/stt -> (command:[words]|started|stopped|error)


import os, sys, time, traceback, base64, argparse, configparser, re
import lib.helper as helper
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *


parser = argparse.ArgumentParser(description="Speech-To-Text engine using CMUSphinx and PocketSphinx\nWhen a hotword is detected, it starts to transcribe text", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config)
config = config["stt"]


if "--test" in sys.argv:
	import pyaudio

	p = pyaudio.PyAudio()
	print("======= ALL DEVICES")
	for i in range(p.get_device_count()):
		print(p.get_device_info_by_index(i))
	print("======= DEFAULT DEVICE")
	print(p.get_default_input_device_info())
	exit(0)


def hotword_callback(client, userdata, message):
	global record_phrases
	message.payload = message.payload.decode()

	if message.payload == "detected":
		record_phrases = True

def phrase_callback(phrase):
	mqtt.publish("jarvis/stt", "command:" + str(phrase))

def mic_buffer_callback(client, userdata, message):
	global decoder, utt_started
	try:
		if message.payload.decode() == "end":
			decoder.end_utt()
			helper.log("stt", "stopping utterance")
			utt_started = False
			process_stt()
		else:
			if not utt_started:
				decoder.start_utt()
				helper.log("stt", "starting utterance")
				utt_started = True
			chunk = base64.b64decode(message.payload.decode())
			decoder.process_raw(chunk, False, False)
	except Exception:
		print("exception:")
		traceback.print_exc()

def process_stt():
	global decoder
	hypothesis_raw = " ".join([seg.word.lower() for seg in decoder.seg()])
	hypothesis = clean_tags(hypothesis_raw)
	print("-> best hypothesis: {}".format(hypothesis_raw))
	mqtt.publish("jarvis/stt", "command:" + hypothesis)

def clean_tags(raw_txt):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr, '', raw_txt)
	return cleantext


mqtt = helper.MQTT(client_id="stt.py")
mqtt.on_message(hotword_callback)
mqtt.subscribe("jarvis/hotword")

mqtt2 = helper.MQTT(client_id="stt.py:mic_buffer")
mqtt2.on_message(mic_buffer_callback)
mqtt2.subscribe("jarvis/internal/mic_buffer_stream")


helper.log("stt", "starting pocketsphinx passively")
mqtt.publish("jarvis/stt", "started")


utt_started = False

decoder_config = Decoder.default_config()
decoder_config.set_string('-hmm', config["acoustic_model"])
decoder_config.set_string('-lm', config["language_model"])
decoder_config.set_string('-dict', config["dictionary"])
decoder = Decoder(decoder_config)

try:
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	mqtt.publish("jarvis/stt", "stopped")
	exit(0)