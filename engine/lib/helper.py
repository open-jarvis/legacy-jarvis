#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import paho.mqtt.client as mqtt
import time

def log(type, msg):
	print("[" + time.strftime("%D %H:%M:%S", time.localtime(time.time())) + "] [" + str(type) + "] " + (" " * (5-len(type))) + str(msg))




class MQTT():
	def __init__(self, host="127.0.0.1", port=1883):
		self.host = host
		self.port = port
		log("mqtt", "creating client")
		self.client = mqtt.Client()
		log("mqtt", "connecting to '" + str(self.host) + ":" + str(self.port) + "'")
		self.client.connect(self.host, self.port)
		log("mqtt", "starting event loop")
		self.client.loop_start()


	"""
	on_connect(client, userdata, flags, rc)
	"""
	def on_connect(self, fn):
		log("mqtt", "adding 'on_connect' callback")
		self.client.on_connect = fn


	"""
	on_message(client, userdata, message)
	"""
	def on_message(self, fn):
		log("mqtt", "adding 'on_message' callback")
		log("mqtt", "calling 'on_message' once to see if it works:")
		fn("dummyclient", "dummydata", "dummymessage")
		self.client.on_message = fn


	def publish(self, topic, payload):
		log("mqtt", "publishing message: " + str(self.host) + ":" + str(self.port) + " " + str(topic) + " '" + str(payload) + "'")
		self.client.publish(topic, payload)


	"""
	arguments:
		callback_function	:	a function with fn(client, userdata, message)
		topic				:	a mqtt topic (for example: test/log)
		host				:	subscribe to messages on that host
	"""
	def subscribe(self, topic):
		log("mqtt", "subscribing to " + str(self.host) + ":" + str(self.port) + " " + str(topic))
		self.client.subscribe(topic)