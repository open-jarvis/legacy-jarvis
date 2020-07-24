#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## hotword.py - listenes for the hotword and sends a mqtt message
## snowboy.kitt.ai

import lib.helper as helper
import lib.snowboy.snowboydecoder as snowboy
import sys

helper.test()

interrupted = False

def signal_handler(signal, frame):
	global interrupted
	interrupted = True

def interrupt_callback():
	global interrupted
	return interrupted

if len(sys.argv) == 1:
	print("Error: need to specify model name")
	print("Usage: python demo.py your.model")
	sys.exit(-1)

	model = sys.argv[1]
sys.exit(1)

detector = snowboy.HotwordDetector(model, sensitivity=0.5)
print('Listening... Press Ctrl+C to exit')

detector.start(	detected_callback=snowboy.ding_callback,
				interrupt_check=interrupt_callback,
				sleep_time=0.03)

detector.terminate()
