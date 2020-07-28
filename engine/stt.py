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
from pocketsphinx import LiveSpeech, get_model_path

def hotword_callback(client, userdata, message):
    if message.payload == "detected":
        log("stt", "hotword received")

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

        start = time.time()

        for phrase in speech:
            print(phrase)



mqtt = MQTT(client_id="jarvis.stt")
mqtt.on_message(hotword_callback)
mqtt.subscribe("jarvis/hotword")
