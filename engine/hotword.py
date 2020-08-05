#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

## hotword.py - listenes for the hotword and sends a mqtt message
## hotword.py uses https://snowboy.kitt.ai/

## input: nothing
## raw_output: jarvis/internal/mic_buffer_stream -> raw bytes mic buffer stream
## output: jarvis/hotword -> (detected|started|stopped|error|direction:[degrees])


import signal, os, sys, time, collections, configparser, argparse, traceback, base64, webrtcvad
import numpy as np

import lib.helper as helper
import lib.snowboy.examples.Python3.snowboydecoder as snowboy
import lib.snowboy.examples.Python3.snowboydetect as snowboydetect
from lib.doa.gcc_phat import gcc_phat
from lib.doa.mic_array import MicArray 


parser = argparse.ArgumentParser(description="Hotword listener using KITT.ai snowboy\nListens for a hotword and publishes MQTT messages", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.config)
config = config["hotword"]


MODEL_PATH = config["model"]
RESOURCE_PATH = config["resource"]
SENSITIVITY = config["sensitivity"]
RATE = 16000
CHANNELS = 4
KWS_FRAMES = 10     # ms
DOA_FRAMES = 800    # ms


mqtt = helper.MQTT(client_id="hotword.py")
hotword_detected = False


if "--no-doa" in sys.argv:
	helper.log("hotword", "Not using Direction of Arrival")
	helper.log("hotword", "This feature hasn't been implemented yet...")

	interrupted = False

	def detected_callback():
		global interrupted, mqtt
		mqtt.publish("jarvis/hotword", "detected")
		
		mqtt.publish("jarvis/lights", "mode:doa")
		time.sleep(10)
		mqtt.publish("jarvis/lights", "off")


	def signal_handler(signal, frame):
		global interrupted, mqtt
		interrupted = True
		mqtt.publish("jarvis/hotword", "stopped")
		exit(0)
		

	def interrupt_callback():
		global interrupted
		return interrupted


	if not os.path.isfile(MODEL_PATH):
		mqtt.publish("jarvis/hotword", "error")
		helper.log("hotword", "model doesn't exist at {}".format(MODEL_PATH))
		sys.exit(-1)


	signal.signal(signal.SIGINT, signal_handler)
	detector = snowboy.HotwordDetector(MODEL_PATH, sensitivity=SENSITIVITY)
	mqtt.publish("jarvis/hotword", "started")


	detector.start(	detected_callback=detected_callback,
					interrupt_check=interrupt_callback,
					sleep_time=0.03)

	detector.terminate()
else:
	detector = snowboydetect.SnowboyDetect(RESOURCE_PATH.encode(), MODEL_PATH.encode())
	detector.SetAudioGain(float(config["gain"]))
	detector.SetSensitivity(SENSITIVITY.encode())

	vad = webrtcvad.Vad(int(config["vad_sensitivity"]))
	speech_count = 0
	speech_detected = 0
	currently_speaking = False

	history = collections.deque(maxlen=int(DOA_FRAMES / KWS_FRAMES))

	raw_file_name = "recording-{}.raw".format(time.strftime("%H-%M-%S", time.localtime(time.time())))

	try:
		with MicArray(RATE, CHANNELS, RATE * KWS_FRAMES / 1000) as mic:
			for chunk in mic.read_chunks():
				history.append(chunk)
				ans = detector.RunDetection(chunk[0::CHANNELS].tostring())

				if vad.is_speech(chunk[0::CHANNELS].tobytes(), RATE):				# if speech got detected
					if not currently_speaking:										## if not speaking yet,
						helper.log("hotword", "voice activity detected", True)		## log that speaking started
					speech_count += 1
					speech_detected = time.time()
					currently_speaking = True

				if time.time() - speech_detected > 1:								# if more than 1 second(s) silence
					if currently_speaking:											## if the user spoke before
						helper.log("hotword", "voice activity ended", True)			## log that speaking ended
					if hotword_detected and currently_speaking:						## if the user said the hotword and spoke before
						helper.log("hotword", "stop transmitting speech")			## log that we won't send any more data to stt.py
						mqtt.publish("jarvis/internal/mic_buffer_stream", "end")	## stop sending data to stt.py
						mqtt.publish("jarvis/lights", "off")
						hotword_detected = False
						os.system("sox -r 16000 -c 1 -b 16 -e signed-integer -t raw {} -t wav {} ; rm {}".format(raw_file_name, raw_file_name.replace(".raw", ".wav"), raw_file_name))
					currently_speaking = False

				if hotword_detected and currently_speaking:							# if the user said the hotword and speaks
					mqtt.publish(	"jarvis/internal/mic_buffer_stream",			## send data to stt.py 
									base64.b64encode(chunk[0::1]), 
									disable_log=True	)
					with open(raw_file_name, "ab") as wavf:							## record the voice
						wavf.write(chunk)

				if ans > 0:
					frames = np.concatenate(history)
					direction = mic.get_direction(frames)
					mqtt.publish("jarvis/hotword", "detected")
					mqtt.publish("jarvis/lights", "direction:" + str(direction))
					mqtt.publish("jarvis/lights", "on")
					helper.log("hotword", "start transmitting speech")
					hotword_detected = True
					raw_file_name = "recording-{}.raw".format(time.strftime("%H-%M-%S", time.localtime(time.time())))
	except KeyboardInterrupt:
		exit(1)
	except Exception as e:
		traceback.print_exc()
		mqtt.publish("jarvis/hotword", "error")
		helper.log("hotword", "mic already in use")
		exit(1)
