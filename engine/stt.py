#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## stt.py - listenes for the hotword and sends a mqtt message
## stt.py uses https://cmusphinx.github.io/

## input: jarvis/hotword -> detected
## output: jarvis/stt -> (command:[words]|started|stopped|error)


import os, sys, time, traceback
import lib.helper as helper 
from pocketsphinx import LiveSpeech

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


record_phrases = False

mqtt = helper.MQTT(client_id="stt.py")
mqtt.on_message(hotword_callback)
mqtt.subscribe("jarvis/hotword")


helper.log("stt", "starting pocketsphinx passively")
mqtt.publish("jarvis/stt", "started")


try:
	start = time.time()
	speech = LiveSpeech(
		verbose=True,
		sampling_rate=16000,
		buffer_size=2048,
		no_search=False,
		full_utt=False,
		hmm="/home/pi/jarvis/resources/stt/acoustic_model/",
		lm="/home/pi/jarvis/resources/stt/german.lm.bin",
		dict="/home/pi/jarvis/resources/stt/german.commands.dict"
	)
	
	phrases = []
	end = time.time()
	helper.log("stt", "took {}s to start stt engine".format(end-start))

	for phrase in speech:
		phrases.append((time.time(), phrase))
		helper.log("stt", "recorded phrase: '" + phrase + "'")
		if record_phrases:
			phrase_callback(phrase)
except Exception:
	traceback.print_exc()
	mqtt.publish("jarvis/stt", "error")
	exit(1)


mqtt.publish("jarvis/stt", "stopped")