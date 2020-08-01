#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## stt.py - listenes for the hotword and sends a mqtt message
## stt.py uses https://cmusphinx.github.io/

## input: jarvis/hotword -> detected
## output: jarvis/stt -> (:[words]|started|stopped|error)

# stop reading input after this second count of silence
END_OF_INPUT_AFTER_SECONDS = 2

import os
import time
from lib.helper import *
from pocketsphinx import LiveSpeech


def hotword_callback(client, userdata, message):
	
	message.payload = message.payload.decode()

	print("mqtt received something")

	log("mqtt", "received message '" + str(message.payload) + "' from topic '" + str(message.topic) + "'")

	if message.payload == "detected":
		log("stt", "hotword received")
		log("stt", "start transcribing")

		speech = LiveSpeech(
			verbose=False,
			sampling_rate=16000,
			buffer_size=2048,
			no_search=False,
			full_utt=False,
			audio_device=0,
			hmm="/home/pi/jarvis/resources/stt/acoustic_model/",
			lm="/home/pi/jarvis/resources/stt/german.lm.bin",
			dic="/home/pi/jarvis/resources/stt/german.min.dict"
		)

		for phrase in speech:
			print(phrase)



mqtt = MQTT(client_id="jarvis.stt")
mqtt.on_message(hotword_callback)
mqtt.subscribe("jarvis/hotword")

while True:
	time.sleep(0.1)