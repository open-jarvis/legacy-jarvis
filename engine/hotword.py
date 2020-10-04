#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: hotword.py [-h] [--config CONFIG]
# 
# Hotword listener using KITT.ai snowboy
# Listens for a hotword and publishes MQTT messages
# 
# optional arguments:
#   -h, --help       show this help message and exit
#   --config CONFIG  Path to jarvis configuration file


## input: nothing
## raw_output: jarvis/internal/mic_buffer_stream -> raw bytes mic buffer stream
## output: jarvis/hotword -> (detected|started|stopped|error|direction:[degrees]|voice_activity_start|voice_activity_end)


## import global packages
import signal, os, sys, time, collections, configparser, argparse, traceback, base64, webrtcvad
import numpy as np


## import helper packages 
import lib.helper as helper
import lib.snowboy.examples.Python3.snowboydecoder as snowboy
import lib.snowboy.examples.Python3.snowboydetect as snowboydetect
from lib.doa.gcc_phat import gcc_phat
from lib.doa.mic_array import MicArray


## add a description and arguments
parser = argparse.ArgumentParser(description="Hotword listener using KITT.ai snowboy\nListens for a hotword and publishes MQTT messages", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()


## take the config file from the argument list and read the configuration
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(args.config)
config = config["hotword"]


## define global final variables
MODEL_PATH						= config["model"]
RESOURCE_PATH					= config["resource"]
SENSITIVITY						= config["sensitivity"]
MAX_VOICE_INACTIVITY_SECONDS	= float(config["max_voice_inactivity_seconds"])
RATE							= 16000
CHANNELS						= 4
KWS_FRAMES						= 10     # ms
DOA_FRAMES						= 800    # ms


## initialize a mqtt client
mqtt = helper.MQTT(client_id="hotword.py")


## initialize the snowboydetect engine. use the RESOURCE_PATH (*.res) and MODEL_PATH (*.hotword)
detector = snowboydetect.SnowboyDetect(RESOURCE_PATH.encode(), MODEL_PATH.encode())
detector.SetAudioGain(float(config["gain"]))
detector.SetSensitivity(SENSITIVITY.encode())
hotword_detected = False
history = collections.deque(maxlen=int(DOA_FRAMES / KWS_FRAMES))


## webrtcvad is being used to detect voice activity
vad = webrtcvad.Vad(int(config["vad_sensitivity"]))
speech_count = 0
speech_detected = 0
currently_speaking = False


# mainloop
try:			
	with MicArray(RATE, CHANNELS, RATE * KWS_FRAMES / 1000) as mic:
		mqtt.publish("jarvis/hotword", "started")

		# read raw microphone chunks
		for chunk in mic.read_chunks():
			history.append(chunk)


			# check if the user said the hotword
			ans = detector.RunDetection(chunk[0::CHANNELS].tostring())


			# if speech gets detected
			if vad.is_speech(chunk[0::CHANNELS].tobytes(), RATE):
				if not currently_speaking:
					helper.log("hotword", "voice_activity_start", True)
				speech_count += 1
				# save the current time (used in combination with MAX_VOICE_INACTIVITY_SECONDS)
				speech_detected = time.time()
				# disable the log message the next loop run (to prevent log flooding)
				currently_speaking = True


			# if the user was silent for at least MAX_VOICE_INACTIVITY_SECONDS
			if time.time() - speech_detected > MAX_VOICE_INACTIVITY_SECONDS:
				if currently_speaking:
					# log a message when the user stopped speaking
					helper.log("hotword", "voice_activity_end", True)

				# if the user said the hotword, gave a command and stopped talking now
				if hotword_detected and currently_speaking:
					# stop transmitting raw speech data to stt.py
					helper.log("hotword", "stop transmitting speech")
					mqtt.publish("jarvis/internal/mic_buffer_stream", "end")
					# turn off the lights
					mqtt.publish("jarvis/lights", "off")
					hotword_detected = False
				currently_speaking = False


			# if the hotword got detected and the user is still giving commands
			if hotword_detected and currently_speaking:
				# send data to the stt.py backend
				# logging is disabled to prevent log flooding
				mqtt.publish(	"jarvis/internal/mic_buffer_stream",
								base64.b64encode(chunk),
								disable_log=True	)


			# if the hotword got detected
			if ans > 0:
				# concatenate all the recorded frames
				frames = np.concatenate(history)
				# calculate the direction (in degrees) the voice came from
				direction = mic.get_direction(frames)
				# notify the subscribers, that the hotword got detected
				mqtt.publish("jarvis/hotword", "detected")
				# tell lights.py the direction and turn on the leds
				mqtt.publish("jarvis/lights", "direction:" + str(direction))
				mqtt.publish("jarvis/lights", "on")
				# next round we'll start transmitting speech
				helper.log("hotword", "start transmitting speech")
				hotword_detected = True
except KeyboardInterrupt:
	mqtt.publish("jarvis/hotword", "error")
	mqtt.publish("jarvis/hotword", "stopped")
	exit(1)
except Exception as e:
	traceback.print_exc()
	helper.log("hotword", "mic already in use")
	mqtt.publish("jarvis/hotword", "error")
	mqtt.publish("jarvis/hotword", "stopped")
	exit(1)
