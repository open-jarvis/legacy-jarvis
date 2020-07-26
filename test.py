#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import engine.lib.helper as helper
import engine.lib.apa102
import time

lights = helper.Lights()
lights.set( ["red", 0, 0, "green", 0, 0, "blue", 0, 0, "yellow", 0, 0] )
lights.on()

i = 0
while i < 50:
	time.sleep(0.075)
	lights.rotate()
	i += 1

lights.off()