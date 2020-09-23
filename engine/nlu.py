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
## output: jarvis/nlu -> (started|stopped|error|intent:[intent]:probability:[probability]:slots:[slots])


## import global packages
import io, os, sys, time, json, argparse, configparser
import urllib.parse as urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer


## import local packages
import lib.helper as helper
import snips_nlu


port = 1884


class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','text/plain')
		self.end_headers()
		
		path = self.path.split("?")[0]
		arguments = urlparse.parse_qs((urlparse.urlparse(self.path)).query)

		if path == "/execute":
			try:
				cmd = arguments["command"][0]
				self.wfile.write(json.dumps({"success":True,"message":runSnipsOnce(cmd)}).encode())
			except KeyError:
				self.wfile.write(json.dumps({"success":False,"message":"need to set 'command' url argument"}).encode())

# this function is being called when the stt engine detects a command
def handler(client, userdata, message):
	global nlp, mqtt
	data = message.payload.decode()
	if data.startswith("command:"):
		command = data.split(":")[1]
		parsed = nlu.parse(command)
		mqtt.publish("jarvis/nlu", json.dumps(parsed))

def runSnipsOnce(cmd):
	global snips_nlu, config
	with io.open(config["dataset"]) as f:
		dataset = json.load(f)
	dataset = helper.transform_dataset(dataset)
	nlu = snips_nlu.SnipsNLUEngine(dataset)
	nlu = nlu.fit(dataset)
	return nlu.parse(cmd)


# add a description and parse arguments
parser = argparse.ArgumentParser(description="Natural language understanding engine using snips-nlu\nConvert spoken language into a command (skill) and arguments", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
parser.add_argument("--message", type=str, help="A string to run against the NLU (Might take several seconds)")
args = parser.parse_args()


# get the config file from argparse and read it
config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
config.read(args.config)
config = config["nlu"]


if args.message is not None:
	print(runSnipsOnce(args.message))
	exit(0)


# initialize mqtt/webserver instance
mqtt = helper.MQTT(client_id="nlu.py")
mqtt.on_message(handler)
mqtt.subscribe("jarvis/stt")
server = HTTPServer(('', port), Handler)

# mark as started
mqtt.publish("jarvis/nlu", "started")



# start snips instance
with io.open(config["dataset"]) as f:
	dataset = json.load(f)

dataset = helper.transform_dataset(dataset)



helper.log("nlu", "training nlu engine")
start = time.time()

nlu = snips_nlu.SnipsNLUEngine(dataset)
nlu = nlu.fit(dataset)

helper.log("nlu", "fininshed training (took {}s)".format(time.time()-start))
mqtt.publish("jarvis/nlu", "started")



if args.message is not None:
	parsed = nlu.parse(args.message)
	print(json.dumps(parsed))
	exit(0)


# mainloop
while True:
	server.handle_request()