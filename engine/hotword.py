#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## hotword.py - listenes for the hotword and sends a mqtt message
## snowboy.kitt.ai

## input: nothing
## output: jarvis/hotword -> (detected|started|stopped)

import lib.snowboy.snowboydetect as snowboydetect
import lib.snowboy.snowboydecoder as snowboy
import sys, signal

interrupted = False

def detected_callback():
	print("hotword detected!")

def signal_handler(signal, frame):
	global interrupted
	interrupted = True

def interrupt_callback():
	global interrupted
	return interrupted

if len(sys.argv) == 1:
	print("Error: need to specify model name")
	print("Usage: python3 " + sys.argv[0] + " model.hotword")
	sys.exit(-1)


model = sys.argv[1]
signal.signal(signal.SIGINT, signal_handler)


detector = snowboy.HotwordDetector(model, sensitivity=0.5)
print('Listening... Press Ctrl+C to exit')

detector.start(	detected_callback=detected_callback,
				interrupt_check=interrupt_callback,
				sleep_time=0.03)

detector.terminate()
