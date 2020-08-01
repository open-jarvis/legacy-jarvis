#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## lights.py - listenes on the mic and controls the leds (calculates doa but has other functionalities too)

## input: jarvis/lights -> (on|off|color:#ff3f3f|basecolor:#ffffff|mode:[doa,static])
## output: nothing

import lib.helper as helper
from lib.doa.gcc_phat import gcc_phat
from lib.doa.mic_array import MicArray
import numpy as np
import time, sys, collections


## lights.py variables
COLOR = [0, 255, 255]
BASECOLOR = [255, 255, 255]
OPACITY = 0.5



def handler(client, userdata, message):
	global lights, COLOR, BASECOLOR, OPACITY, MODE
	data = message.payload.decode()

	print("handler")

	if data == "on":
		lights.on()
	if data == "off":
		lights.off()
	if data.startsWith("color:"):
		h = data.split(":").lstrip('#')
		COLOR = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
	if data.startsWith("basecolor:"):
		h = data.split(":")[1].lstrip('#')
		BASECOLOR = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
	if data.startsWith("mode:"):
		MODE = data.split(":")[1]


lights = helper.Lights()

mqtt = helper.MQTT(client_id="lights.py")
mqtt.on_message(handler)
mqtt.subscribe("jarvis/lights")

while True:
	time.sleep(1)