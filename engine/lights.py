#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## lights.py - listenes on the mic and controls the leds (calculates doa but has other functionalities too)

## input: jarvis/hotword -> (detected|direction:[degrees])
## output: nothing


import lib.helper as helper
from lib.doa.gcc_phat import gcc_phat
from lib.doa.mic_array import MicArray
import numpy as np
import time, sys, collections, argparse, configparser, traceback, math


def handler(client, userdata, message):
	global lights, animation, direction, position
	data = message.payload.decode()

	try:
		if data == "detected":
			led_circle = ["main"]
			for i in range(len(GRADIENTS)):
				lights.add_color("gradient" + str(i), GRADIENTS[i])
				led_circle.append("gradient" + str(i))

			led_circle.append("secondary")

			for i in range(len(GRADIENTS)-1, -1, -1):
				led_circle.append("gradient" + str(i))

			for i in range(12 - len(GRADIENTS)*2 - 2):
				led_circle.append("main")

			lights.set(led_circle)
			lights.rotate(-position + SPREAD)
			lights.on()

			helper.log("lights", "turning on led circle at degree:position {}:{}".format(direction, position))

		if data == "off":
			lights.off()

		if data.startswith("direction:"):
			direction = int(float(data.split(":")[1]))
			position = int((direction + 15) % 360 / 30) % 12
	except Exception as e:
		traceback.print_exc()
	

def calculate_led_circle(main, secondary, gradients, direction):
	led_data = [[0] + _ for _ in gradients] + [0] + secondary + [[0] + _ for _ in gradients[::-1]] + ([0] + main) * (12 - 2*len(gradients) - 1)
	return helper.flatten(led_data)

def calculate_gradients(main, secondary, spread):
	gradients = [ [0,0,0] ] * spread
	for i in range(spread):
		gradients[i] = [
			int(main[0] + ((abs(secondary[0] - main[0]) / (spread + 1)) * (i+1))),
			int(main[1] + ((abs(secondary[1] - main[1]) / (spread + 1)) * (i+1))),
			int(main[2] + ((abs(secondary[2] - main[2]) / (spread + 1)) * (i+1)))
		]
	return gradients


parser = argparse.ArgumentParser(description="Jarvis Lights API for ReSpeaker 4-Mic Array\nControls the lights and animations", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config)

animation = configparser.ConfigParser()
animation.read(config["lights"]["animation"])


SLEEP_DURATION	= float(animation["animation"]["sleep_duration"])
SPREAD			= int(animation["animation"]["spread"])
WIDTH			= int(animation["animation"]["width"])
TYPE			= animation["animation"]["type"]
MAIN_COLOR		= [int(numeric_string) for numeric_string in animation["colors"]["main"].split(",")]
SECONDARY_COLOR	= [int(numeric_string) for numeric_string in animation["colors"]["secondary"].split(",")]
GRADIENTS		= calculate_gradients(MAIN_COLOR, SECONDARY_COLOR, SPREAD)
direction		= 0
position		= 0


lights = helper.Lights()
lights.add_color("main", MAIN_COLOR)
lights.add_color("secondary", SECONDARY_COLOR)

mqtt = helper.MQTT(client_id="lights.py")
mqtt.on_message(handler)
mqtt.subscribe("jarvis/hotword")


while True:	# main loop
	time.sleep(1)