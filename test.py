#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import engine.lib.helper as helper
import time

mqtt = helper.MQTT()

def mqtt_callback(client, userdata, message):
	print("MQTT:")
	print(client)
	print(userdata)
	print(message)
	print("=== END ===")

mqtt.on_message = mqtt_callback
mqtt.subscribe("test/log")
mqtt.connect()

while True:
	mqtt.publish("test/log", "it is: " + str(int(time.time())))
	time.sleep(3)