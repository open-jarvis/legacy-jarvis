#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: lights.py [-h] [--config CONFIG]
# 
# Jarvis Lights API for ReSpeaker 4-Mic Array
# Controls the lights and animations
# 
# optional arguments:
#   -h, --help       show this help message and exit
#   --config CONFIG  Path to jarvis configuration file


## input: jarvis/lights -> (on|off|direction:[degrees])
## output: jarvis/lights -> (started|error|stopped)


## import global packages
import lib.helper as helper
from lib.doa.gcc_phat import gcc_phat
from lib.doa.mic_array import MicArray
import numpy as np
import time, sys, collections, argparse, configparser, traceback, math


# this function gets called whenever the jarvis/lights mqtt listener receives a message
def handler(client, userdata, message):
	global lights, animation, direction, position

	# read the mqtt data
	data = message.payload.decode()
	
	try:
		# if a user wants to turn on the lights
		if data == "on":
			# TODO: add different animations

			# calulate gradients for the leds
			led_circle = ["main"]
			for i in range(len(GRADIENTS)):
				lights.add_color("gradient" + str(i), GRADIENTS[i])
				led_circle.append("gradient" + str(i))

			led_circle.append("secondary")

			for i in range(len(GRADIENTS)-1, -1, -1):
				led_circle.append("gradient" + str(i))

			for i in range(12 - len(GRADIENTS)*2 - 2):
				led_circle.append("main")

			# set the leds and rotate to match the destination of arrival
			lights.set(led_circle)
			lights.rotate(-position + SPREAD)
			lights.on()

			# print a logging message
			helper.log("lights", "turning on led circle at degree:position {}:{}".format(direction, position))

		# if a user wants to turn off the lights
		if data == "off":
			lights.off()

		# if the user wants to set a direction of arrival
		if data.startswith("direction:"):
			# calculate the position (number of leds) when a direction (degrees) is given
			direction = int(float(data.split(":")[1]))
			position = int((direction + 15) % 360 / 30) % 12
	except Exception as e:
		# print an exception and log the error
		traceback.print_exc()
		helper.log("lights", "Failed to set lights: " + traceback.format_exc())


# calulates gradient for for a given main color, secondary color and a integer spread
def calculate_gradients(main, secondary, spread):
	gradients = [ [0,0,0] ] * spread
	for i in range(spread):
		gradients[i] = [
			int(main[0] + ((abs(secondary[0] - main[0]) / (spread + 1)) * (i+1))),
			int(main[1] + ((abs(secondary[1] - main[1]) / (spread + 1)) * (i+1))),
			int(main[2] + ((abs(secondary[2] - main[2]) / (spread + 1)) * (i+1)))
		]
	return gradients


# initialize an argument parser, add a description and arguments
parser = argparse.ArgumentParser(description="Jarvis Lights API for ReSpeaker 4-Mic Array\nControls the lights and animations", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()


# get the config file from the argparser and read it
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(args.config)


# read the animation config from the above config file
animation = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
animation.read(config["lights"]["animation"])


# define global final variables
SLEEP_DURATION	= float(animation["animation"]["sleep_duration"])
SPREAD			= int(animation["animation"]["spread"])
WIDTH			= int(animation["animation"]["width"])
TYPE			= animation["animation"]["type"]
MAIN_COLOR		= [int(numeric_string) for numeric_string in animation["colors"]["main"].split(",")]
SECONDARY_COLOR	= [int(numeric_string) for numeric_string in animation["colors"]["secondary"].split(",")]
GRADIENTS		= calculate_gradients(MAIN_COLOR, SECONDARY_COLOR, SPREAD)
direction		= 0
position		= 0


# initialize the lights
lights = helper.Lights()
lights.add_color("main", MAIN_COLOR)
lights.add_color("secondary", SECONDARY_COLOR)


# initialize a mqtt client and add a callback
mqtt = helper.MQTT(client_id="lights.py")
mqtt.on_message(handler)
mqtt.subscribe("jarvis/lights")
mqtt.publish("jarvis/lights", "started")


# mainloop
while True:
	time.sleep(1)

mqtt.publish("jarvis/lights", "stopped")