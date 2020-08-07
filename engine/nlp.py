#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: nlp.py [-h] [--config CONFIG]
# 
# Natural language processing engine using spaCy
# Convert spoken language into a command (skill) and arguments
# 
# optional arguments:
#   -h, --help       show this help message and exit
#   --config CONFIG  Path to jarvis configuration file


## input: jarvis/stt -> command:[words]
## output: jarvis/nlp -> (started|stopped|error|skill:[skill]:arguments[arguments])


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
		doc = nlp(command)
		for token in doc:
			print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
					token.shape_, token.is_alpha, token.is_stop)


# add a description and parse arguments
parser = argparse.ArgumentParser(description="Natural language processing engine using spaCy\nConvert spoken language into a command (skill) and arguments", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()


# get the config file from argparse and read it
config = configparser.ConfigParser()
config.read(args.config)
config = config["nlp"]


# initialize nlp instance
nlp = spacy.load(config["model"])


#initialize mqtt instance
mqtt = helper.MQTT(client_id="nlp.py")
mqtt.on_message(handler)
mqtt.subscribe("jarvis/stt")


# mark as started
mqtt.publish("jarvis/nlp", "started")


# mainloop
while True:
	time.sleep(1)