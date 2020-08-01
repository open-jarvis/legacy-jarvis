#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## hotword.py - listenes for the hotword and sends a mqtt message
## hotword.py uses https://snowboy.kitt.ai/

## input: nothing
## output: jarvis/hotword -> (detected|started|stopped|error)


MODEL_PATH = "/home/pi/jarvis/resources/hotword/alexa.hotword"
SENSITIVITY = 0.2					## 0.6 - a lot of false positives			## 0.05 - works good...


import lib.helper as helper
import lib.snowboy.examples.Python3.snowboydecoder as snowboy
import signal, os, sys, time


mqtt = helper.MQTT(client_id="hotword")
lights = helper.Lights()


interrupted = False


def detected_callback():
	global interrupted, mqtt, lights
	mqtt.publish("jarvis/hotword", "detected")
	lights.add_color("newcolor", [ 255, 200, 60 ])
	lights.set( [ "yellow", 0, 0, "red", 0, 0, "green", 0, 0, "blue", 0, 0 ] )

	lights.on()
	i = 0
	while i < 20:
		if interrupted:
			exit(0)
		else:
			lights.rotate()
			time.sleep(0.06)
			i += 1
	lights.off()


def signal_handler(signal, frame):
	global interrupted, lights, mqtt
	interrupted = True
	mqtt.publish("jarvis/hotword", "stopped")
	lights.off()
	exit(0)
	

def interrupt_callback():
	global interrupted
	return interrupted


if not os.path.isfile(MODEL_PATH): 
	mqtt.publish("jarvis/hotword", "error")
	helper.log("hotw", "model doesn't exist at {}".format(MODEL_PATH))
	sys.exit(-1)


signal.signal(signal.SIGINT, signal_handler)
detector = snowboy.HotwordDetector(MODEL_PATH, sensitivity=SENSITIVITY)
mqtt.publish("jarvis/hotword", "started")


detector.start(	detected_callback=detected_callback,
				interrupt_check=interrupt_callback,
				sleep_time=0.03)


detector.terminate()
