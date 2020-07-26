#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## hotword.py - listenes for the hotword and sends a mqtt message
## hotword.py uses https://snowboy.kitt.ai/

## input: nothing
## output: jarvis/hotword -> (detected|started|stopped|error)


import lib.helper as helper
import sys


mqtt = helper.MQTT(client_id="hotword")


if sys.version_info[0] != 2:
	mqtt.publish("jarvis/hotword", "error")
	helper.log("hotw", "hotword.py must be run with python 2")
	sys.exit(-1)


import lib.snowboy.snowboydetect as snowboydetect
import lib.snowboy.snowboydecoder as snowboy
import signal


interrupted = False


def detected_callback():
	mqtt.publish("jarvis/hotword", "detected")


def signal_handler(signal, frame):
	global interrupted
	interrupted = True

def interrupt_callback():
	global interrupted
	return interrupted


if len(sys.argv) == 1:
	mqtt.publish("jarvis/hotword", "error")
	helper.log("hotw", "no model name specified, exiting")
	sys.exit(-1)


model = sys.argv[1]
signal.signal(signal.SIGINT, signal_handler)
detector = snowboy.HotwordDetector(model, sensitivity=0.5)
mqtt.publish("jarvis/hotword", "started")


detector.start(	detected_callback=detected_callback,
				interrupt_check=interrupt_callback,
				sleep_time=0.03)


detector.terminate()
mqtt.publish("jarvis/hotword", "stopped")