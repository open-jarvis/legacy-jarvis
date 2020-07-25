#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import engine.lib.helper as helper
import time, json

mqtt = helper.MQTT()
mqtt_sender = helper.MQTT()

def mqtt_callback(client, userdata, message):
	try:
		helper.log("mqtt", "received message '" + str(message.payload) + "' from topic '" + str(message.topic) + "'")
	except Exception as e:
		print("error: " + str(e))


mqtt.on_message(mqtt_callback)
mqtt.subscribe("test/log")

while True:
	mqtt_sender.publish("test/log", "it is: " + str(int(time.time())))
	time.sleep(3)