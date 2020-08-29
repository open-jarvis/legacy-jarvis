#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: nlu.py [-h] [--config CONFIG]
# 
# Natural language understanding engine using spaCy and RASA
# Convert spoken language into a command (skill) and arguments
# 
# optional arguments:
#   -h, --help       show this help message and exit
#   --config CONFIG  Path to jarvis configuration file


## input: jarvis/stt -> command:[words]
## output: jarvis/nlu -> (started|stopped|error|skill:[skill]:arguments[arguments])


## import global packages
import os, sys, time, argparse, configparser


## import local packages
import spacy
import lib.helper as helper




# this function is being called when the stt engine detects a command
def handler(client, userdata, message):
	global nlp
	data = message.payload.decode()
	if data.startswith("command:"):
		command = data.split(":")[1]



# add a description and parse arguments
parser = argparse.ArgumentParser(description="Natural language understanding engine using snips-nlu\nConvert spoken language into a command (skill) and arguments", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()


# get the config file from argparse and read it
config = configparser.ConfigParser()
config.read(args.config)
config = config["nlu"]


#initialize mqtt instance
mqtt = helper.MQTT(client_id="nlp.py")
mqtt.on_message(handler)
mqtt.subscribe("jarvis/stt")


# mark as started
mqtt.publish("jarvis/nlp", "started")


# mainloop
while True:
	time.sleep(1)