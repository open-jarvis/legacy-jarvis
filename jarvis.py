#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: jarvis.py [-h] [--config CONFIG]
# 
# Manages all the Jarvis services
# 
# optional arguments:
#   -h, --help       show this help message and exit
#   --config CONFIG  Path to jarvis configuration file


# import global and local packages
import subprocess, os, sys, time, argparse, json, signal, urllib.request
import urllib.parse as urlparse
import engine.lib.helper as helper
from http.server import BaseHTTPRequestHandler, HTTPServer


## add a description and arguments
parser = argparse.ArgumentParser(description="Manages all the Jarvis services", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--status", help="Lists all running services with status", action='store_true')
args = parser.parse_args()


## getting path of jarvis.conf
path = os.path.abspath(os.path.dirname(sys.argv[0]))
jarvis_conf = "{}/jarvis.conf".format(path)
engine_path = "{}/engine".format(path)
log_path = "{}/log".format(path)
status_file = "{}/jarvis.status".format(path)


## http port
port = 1884


## saving info for all services
processes = {
	"hotword":	{ "script": "hotword.py",	"logfile": open("{}/hotword.py.log".format(log_path), "w"),	}, # subprocess.Popen(["python3", "{}/hotword.py".format(engine_path), "--config", jarvis_conf], shell=True),
	"stt":		{ "script": "stt.py",		"logfile": open("{}/stt.py.log".format(log_path), "w"),		}, # subprocess.Popen(["python3", "{}/stt.py".format(engine_path), "--config", jarvis_conf], shell=True),
	"lights":	{ "script": "lights.py",	"logfile": open("{}/lights.py.log".format(log_path), "w"),	}, # subprocess.Popen(["python3", "{}/lights.py".format(engine_path), "--config", jarvis_conf], shell=True),
	"nlu":		{ "script": "nlu.py",		"logfile": open("{}/nlu.py.log".format(log_path), "w"),		}  # subprocess.Popen(["python3", "{}/nlu.py".format(engine_path), "--config", jarvis_conf], shell=True)
}
service_status = {
	"hotword": "Not running",
	"stt": "Not running",
	"lights": "Not running",
	"nlu": "Not running"
}


## show status
if "--status" in sys.argv:
	print("Jarvis status:")
	if os.path.isfile(status_file):
		print("  jarvis .... Running")
	else:
		print("  jarvis .... Not running")
	
	f = open(status_file, "r")
	stati = json.loads(f.read())
	for service in stati:
		print("  {} {} {}".format(service, "." * (10-len(service)), stati[service]))
	exit()


# http handler class
class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','text/json')
		self.send_header('Access-Control-Allow-Origin','*')
		self.end_headers()
		
		path = self.path.split("?")[0]
		arguments = urlparse.parse_qs((urlparse.urlparse(self.path)).query)

		helper.log("jarvis", "http get " + str(self.path))
		if path == "/status":
			try:
				self.wfile.write(json.dumps({"success":True,"message":json.loads(open(status_file, "r").read())}).encode())
			except KeyError:
				self.wfile.write(json.dumps({"success":False,"message":"something failed"}).encode())
			except Exception as e:
				self.wfile.write(json.dumps({"success":False,"message":str(e)}).encode())
		if path == "/execute":
			try:
				cmd = urlparse.quote(arguments["command"][0])
				self.wfile.write(urllib.request.urlopen("http://127.0.0.1:1885/execute?command=" + cmd).read())
			except Exception as e:
				self.wfile.write(json.dumps({"success":False,"message":str(e)}).encode())


# mqtt callback
def handler(client, userdata, message):
	global status_file, service_status
	
	data = message.payload.decode()
	topic = message.topic
	service = topic.split("/")[1]

	if data == "started":
		service_status[service] = "Running"
	if data == "stopped":
		service_status[service] = "Not Running"
	if data == "error":
		service_status[service] = "Error"

	writeStatus()

# helper function to run a command
def runCommand(cmd, logfile):
	return subprocess.Popen(cmd, shell=True, stdout=logfile, stderr=logfile)
	# return subprocess.Popen(cmd.strip().split(), shell=False, stdout=logfile, stderr=logfile)

# helper function to write new status to file
def writeStatus():
	global service_status, processes

	for service in processes:
		if processes[service]["process"].poll() is not None:
			service_status[service] = "Not running"

	f = open(status_file, "w")
	chars = f.write(json.dumps(service_status))
	f.close()

	helper.log("jarvis", "updated status file: wrote " + str(chars) + " chars")

# exit function
def exitCleanly(signalNumber, frame):
	print("received signal with number " + str(signalNumber))
	global processes
	helper.log("jarvis", "stopping because of user signal")
	print("stopping because of user signal")

	os.remove(status_file)

	for service in processes:
		print("stopping " + str(service) + " ...")
		processes[service]["process"].kill()
		helper.log("jarvis", "stopped service {}".format(service))
	
	exit(0)

# start all the processes
for service in processes:
	processes[service]["process"] = runCommand("{} {}/{} --config {}".format(sys.executable, engine_path, processes[service]["script"], jarvis_conf), processes[service]["logfile"])
	helper.log("jarvis", "started service {}, pid: {}".format(service, processes[service]["process"].pid))


# initialize a mqtt client
mqtt = helper.MQTT(client_id="jarvis.py")
mqtt.on_message(handler)
mqtt.subscribe("jarvis/#")
server = HTTPServer(('', port), Handler)


# register signal handlers
signal.signal(signal.SIGINT, exitCleanly)
signal.signal(signal.SIGTERM, exitCleanly)


# mainloop
i = 0
while 1:
	i += 1
	server.handle_request()
	try:
		for service in processes:
			if processes[service]["process"].poll() is not None:
				# TODO: safely prevent loop
				helper.log("jarvis", "service {} exited unexpectedly, attempting restart".format(service))
				processes[service]["process"] = runCommand("{} {}/{} --config {}".format(sys.executable, engine_path, processes[service]["script"], jarvis_conf), processes[service]["logfile"])
		if i % 50000 == 0:
			writeStatus()
			i = 0
	except KeyboardInterrupt:
		exitCleanly()