#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## hotword.py - listenes for the hotword and sends a mqtt message
## snowboy.kitt.ai

## input: nothing
## output: jarvis/hotword -> (detected|started|stopped|error)


import lib.helper as helper
import lib.snowboy.snowboydetect as snowboydetect
import lib.snowboy.snowboydecoder as snowboy
import sys, signal


interrupted = False
mqtt = helper.MQTT(client_id="hotword")


def detected_callback():
	mqtt.publish("jarvis/hotword", "detected")

def signal_handler(signal, frame):
	global interrupted
	interrupted = True

def interrupt_callback():
	global interrupted
	return interrupted


if len(sys.argv) == 1:
	helper.log("hotw", "no model name specified, exiting")
	mqtt.publish("jarvis/hotword", "error")
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