#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## hotword.py - listenes for the hotword and sends a mqtt message
## hotword.py uses https://snowboy.kitt.ai/

## input: nothing
## output: jarvis/hotword -> (detected|started|stopped|error)


<<<<<<< HEAD
import signal, os, sys, time, collections, configparser, argparse
import numpy as np

import lib.helper as helper
import lib.snowboy.examples.Python3.snowboydecoder as snowboy
import lib.snowboy.examples.Python3.snowboydetect as snowboydetect
from lib.doa.gcc_phat import gcc_phat
from lib.doa.mic_array import MicArray 


parser = argparse.ArgumentParser(description="Hotword listener using KITT.ai snowboy\nListens for a hotword and publishes MQTT messages", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config)


MODEL_PATH = config["hotword"]["model"]
RESOURCE_PATH = config["hotword"]["resource"]
SENSITIVITY = config["hotword"]["sensitivity"]
RATE = 16000
CHANNELS = 4
KWS_FRAMES = 10     # ms
DOA_FRAMES = 800    # ms


mqtt = helper.MQTT(client_id="hotword.py")


if "--no-doa" in sys.argv:
	helper.log("hotw", "Not using Direction of Arrival")
	helper.log("hotw", "This feature hasn't been implemented yet...")
=======
MODEL_PATH = "/home/pi/jarvis/resources/hotword/alexa.hotword"
SENSITIVITY = 0.2					## 0.6 - a lot of false positives			## 0.05 - works good...


import lib.helper as helper
import lib.snowboy.examples.Python3.snowboydecoder as snowboy
import signal, os, sys, time


mqtt = helper.MQTT(client_id="hotword")
lights = helper.Lights()
>>>>>>> stt

	interrupted = False

	def detected_callback():
		global interrupted, mqtt
		mqtt.publish("jarvis/hotword", "detected")
		
		mqtt.publish("jarvis/lights", "mode:doa")
		time.sleep(10)
		mqtt.publish("jarvis/lights", "off")


<<<<<<< HEAD
	def signal_handler(signal, frame):
		global interrupted, mqtt
		interrupted = True
		mqtt.publish("jarvis/hotword", "stopped")
		exit(0)
		
=======
def detected_callback():
	global interrupted, mqtt, lights
	mqtt.publish("jarvis/hotword", "detected")
	lights.add_color("newcolor", [ 255, 200, 60 ])
	lights.set( [ "yellow", 0, 0, "red", 0, 0, "green", 0, 0, "blue", 0, 0 ] )
	# lights.set( [ "newcolor", 0, 0, "newcolor", 0, 0, "newcolor", 0, 0, "newcolor", 0, 0 ] )

	lights.on()
	i = 0
	while i < 50:
		if interrupted:
			exit(0)
		else:
			lights.rotate()
			time.sleep(0.05)
			i += 1
	lights.off()
>>>>>>> stt

	def interrupt_callback():
		global interrupted
		return interrupted

<<<<<<< HEAD
=======
def signal_handler(signal, frame):
	global interrupted, lights, mqtt
	interrupted = True
	mqtt.publish("jarvis/hotword", "stopped")
	lights.off()
	exit(0)
	
>>>>>>> stt

	if not os.path.isfile(MODEL_PATH):
		mqtt.publish("jarvis/hotword", "error")
		helper.log("hotw", "model doesn't exist at {}".format(MODEL_PATH))
		sys.exit(-1)


<<<<<<< HEAD
	signal.signal(signal.SIGINT, signal_handler)
	detector = snowboy.HotwordDetector(MODEL_PATH, sensitivity=SENSITIVITY)
	mqtt.publish("jarvis/hotword", "started")


	detector.start(	detected_callback=detected_callback,
					interrupt_check=interrupt_callback,
					sleep_time=0.03)
=======
if not os.path.isfile(MODEL_PATH): 
	mqtt.publish("jarvis/hotword", "error")
	helper.log("hotw", "model doesn't exist at {}".format(MODEL_PATH))
	sys.exit(-1)


signal.signal(signal.SIGINT, signal_handler)
detector = snowboy.HotwordDetector(MODEL_PATH, sensitivity=SENSITIVITY)
mqtt.publish("jarvis/hotword", "started")
>>>>>>> stt

	detector.terminate()
else:
	detector = snowboydetect.SnowboyDetect(RESOURCE_PATH.encode(), MODEL_PATH.encode())
	detector.SetAudioGain(1)
	detector.SetSensitivity(SENSITIVITY.encode())

	history = collections.deque(maxlen=int(DOA_FRAMES / KWS_FRAMES))

	try:
		with MicArray(RATE, CHANNELS, RATE * KWS_FRAMES / 1000)  as mic:
			for chunk in mic.read_chunks():
				history.append(chunk)
				ans = detector.RunDetection(chunk[0::CHANNELS].tostring())
				if ans > 0:
					frames = np.concatenate(history)
					direction = mic.get_direction(frames)
					mqtt.publish("jarvis/hotword", "detected")
					mqtt.publish("jarvis/lights", "direction:" + str(direction))
					mqtt.publish("jarvis/lights", "on")

<<<<<<< HEAD
	except KeyboardInterrupt:
		pass
=======
detector.terminate()
>>>>>>> stt
