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
import subprocess, os, sys, time, argparse, json, signal, urllib.request, socket, multiprocessing, random, traceback
import paho.mqtt.publish as publish
import urllib.parse as urlparse
import engine.lib.helper as helper
from http.server import BaseHTTPRequestHandler, HTTPServer


## add a description and arguments
parser = argparse.ArgumentParser(description="Manages all the Jarvis services", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--status", help="Lists all running services with status", action='store_true')
parser.add_argument("--stop-all", help="Stops all services", action='store_true')
parser.add_argument("--start-all", help="Starts all services", action='store_true')
args = parser.parse_args()


## getting path of jarvis.conf
path = os.path.abspath(os.path.dirname(sys.argv[0]))
jarvis_conf = "{}/jarvis.conf".format(path)
engine_path = "{}/engine".format(path)
log_path = "{}/log".format(path)


## http port
port = 1884


## saving info for all services
manager = multiprocessing.Manager()
processes = {
	"hotword":	{ "script": "hotword.py" },
	"stt":		{ "script": "stt.py"	 },
	"lights":	{ "script": "lights.py"	 },
	"nlu":		{ "script": "nlu.py"	 }
}
service_status = manager.dict({
	"hotword": "Not running",
	"stt": "Not running",
	"lights": "Not running",
	"nlu": "Not running"
})
registered_devices = manager.list(())
tokens = manager.list(())



######################  COMMAND LINE ARGUMENTS  ############################################
## show status
if "--status" in sys.argv:
	print("Jarvis status:")
	try:
		stati = json.loads(urllib.request.urlopen("http://localhost:" + str(port) + "/status").read())
		if stati["success"]:
			stati = stati["message"]
			for service in stati:
				print("  {} {} {}".format(service, "." * (10-len(service)), stati[service]))
	except Exception:
		print("  jarvis .... Not running")
	exit()
	
## stop all services
if "--stop-all" in sys.argv:
	stati = json.loads(urllib.request.urlopen("http://localhost:" + str(port) + "/stop-all").read())
	if stati["success"]:
		print("ok")
		exit(0)
	else:
		print("error: " + stati["message"])
		exit(1)

## start all services
if "--start-all" in sys.argv:
	stati = json.loads(urllib.request.urlopen("http://localhost:" + str(port) + "/start-all").read())
	if stati["success"]:
		print("ok")
		exit(0)
	else:
		print("error: " + stati["message"])
		exit(1)


######################  PERFORM CHECKS  ############################################
## check if jarvis is already running
try:
	stati = json.loads(urllib.request.urlopen("http://localhost:" + str(port) + "/status").read())
	print("Jarvis is already running.\n\nMake sure all Jarvis instances are stopped")
	exit(1)
except Exception:
	pass


######################  HTTP HANDLER  ############################################
# http handler class
class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		global processes, service_status, tokens, registered_devices

		self.send_response(200)
		self.send_header('Content-type','text/json')
		self.send_header('Access-Control-Allow-Origin','*')
		self.end_headers()
		
		path = self.path.split("?")[0]
		arguments = urlparse.parse_qs((urlparse.urlparse(self.path)).query)

		helper.log("jarvis", "http get " + str(self.path))
		if path == "/status":
			try:
				self.wfile.write(json.dumps({"success":True,"message":service_status.copy()}).encode())
			except KeyError:
				self.wfile.write(json.dumps({"success":False,"message":"an unknown error occured"}).encode())
			except Exception as e:
				self.wfile.write(json.dumps({"success":False,"message":str(e)}).encode())
		if path == "/execute":
			try:
				cmd = urlparse.quote(arguments["command"][0])
				self.wfile.write(urllib.request.urlopen("http://127.0.0.1:1885/execute?command=" + cmd).read())
			except Exception as e:
				self.wfile.write(json.dumps({"success":False,"message":str(e)}).encode())
		if path == "/discovery":
			try:
				self.wfile.write(json.dumps({"success":True, "jarvis": get_ip()}).encode())
			except Exception as e:
				self.wfile.write(json.dumps({"success":True, "jarvis": ""}).encode())
		if path == "/stop-all":
			try:
				publish.single("jarvis/services", "stop-all", hostname="localhost")
				self.wfile.write(json.dumps({"success":True, "message": "stopped"}).encode())
			except Exception as e:
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())
				helper.log("http", "error: /stop-all - {}".format(str(e)))
		if path == "/start-all":
			try:
				publish.single("jarvis/services", "start-all", hostname="localhost")
				self.wfile.write(json.dumps({"success":True, "message": "started"}).encode())
			except Exception as e:
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())
				helper.log("http", "error: /start-all - {}".format(str(e)))
		if path == "/generate-token":
			try:
				new_token = ''.join(random.choice("abcdef0123456789") for _ in range(8))
				expires = int(time.time()) + 120
				tokens.append((new_token, expires))

				i = 0
				for token, extime in tokens:
					if extime < time.time():
						tokens.pop(i)
						helper.log("jarvis", "token {} expired".format(token))
					i += 1

				helper.log("jarvis", "generated token {} expires in {} seconds".format(new_token, expires - int(time.time())))
				self.wfile.write(json.dumps({"success":True, "token": new_token}).encode()) 
			except Exception as e:
				helper.log("http", "error: /generate-token - {}".format(traceback.format_exc().replace("\n", "<br>")))
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())
		if path == "/register-device":
			try:
				ip = self.client_address[0]
				name = arguments["name"][0]
				passed_token = arguments["token"][0]
				dev_type = arguments["type"][0]
				con_type = "app" if (arguments["is_app"][0] == "true") else "web"
				expdate = -1

				i = 0
				token_index = -1
				for token, extime in tokens:
					if token == passed_token:
						expdate = extime
						token_index = i
					i += 1
				
				if (expdate < time.time()):
					if token_index == -1:
						helper.log("jarvis", "token {} not found {} (user tried to auth)".format(passed_token, expdate))
						self.wfile.write(json.dumps({"success":False, "message":"Token invalid!"}).encode())
					else:
						tokens.pop(token_index)
						helper.log("jarvis", "token {} expired {} (user tried to auth)".format(passed_token, expdate))
						self.wfile.write(json.dumps({"success":False, "message":"Token expired!"}).encode())
				else:
					tokens.pop(token_index)
					registered_devices.append({
						"name": name,
						"ip": ip, 
						"type": dev_type, 
						"status": "green", 
						"connection": con_type,
						"id": token
					})
					helper.log("jarvis", "registered new device {} with token {}".format(ip, token))
					self.wfile.write(json.dumps({"success":True, "message": "Congrats! You're registered"}).encode())
			except Exception as e:
				helper.log("http", "error: /register-device - {}".format(traceback.format_exc().replace("\n", "<br>")))
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())
		if path == "/unregister-device":
			token = arguments["token"][0]
			
			try:
				i = 0
				popped = False
				for dev in registered_devices:
					if dev["id"] == token:
						registered_devices.pop(i)
						popped = True
					i += 1

				if popped:
					helper.log("jarvis", "unregistered device with token {}".format(token))
					self.wfile.write(json.dumps({"success":True, "message": "Unregistered!"}).encode())
				else:
					helper.log("jarvis", "couldn't unregister device with token {}: not found".format(token))
					self.wfile.write(json.dumps({"success":False, "message": "Couldn't find device with token {}".format(token)}).encode())
			except Exception as e:
				helper.log("http", "error: /unregister-device - {}".format(traceback.format_exc().replace("\n", "<br>")))
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())
		if path == "/list-devices":
			try:
				self.wfile.write(json.dumps({"success":True, "devices":list(registered_devices)}).encode())
			except Exception as e:
				helper.log("http", "error: /list-devices - {}".format(traceback.format_exc().replace("\n", "<br>")))
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())

			

						

	def log_message(self, format, *args):
		pass
	

######################  FUNCTIONS  ############################################
# gets ip address
def get_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		# doesn't even have to be reachable
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except Exception:
		IP = '127.0.0.1'
	finally:
		s.close()
	return IP

# mqtt callback
def handler(client, userdata, message):
	global service_status
	
	data = message.payload.decode()
	topic = message.topic
	service = topic.split("/")[1]

	if data == "started":
		setServiceRunning(service, "handler::data==started")
	if data == "stopped":
		setServiceNotRunning(service, "handler::data==stopped")
	if data == "error":
		service_status[service] = "Error"

	if topic == "jarvis/services":
		if data == "start-all":
			startProcesses()
		if data == "stop-all":
			stopProcesses()

	updateStatus()


# start all processes
def startProcesses():
	global processes
	for service in processes:
		processes[service]["process"] = runCommand("{} {}/{} --config {}".format(sys.executable, engine_path, processes[service]["script"], jarvis_conf))
		# helper.log("jarvis", "started service {}, pid: {}".format(service, processes[service]["process"].pid))

# stop all processes
def stopProcesses(a="",b=""):
	global processes
	helper.log("jarvis", "stopping processes")

	for service in processes:
		print("stopping " + str(service) + (""*(15-len(service))) + " with pid " + str(processes[service]["process"].pid) + " & pgid " + str(os.getpgid(processes[service]["process"].pid)))
		os.killpg(os.getpgid(processes[service]["process"].pid), signal.SIGTERM)
		helper.log("jarvis", "stopped service {}".format(service))

# helper function for logging
def setServiceNotRunning(service, caller):
	global service_status
	service_status[service] = "Not Running"
	# print("{} set status of {} to Not Running".format(caller, service))

# helper function for logging
def setServiceRunning(service, caller):
	global service_status
	service_status[service] = "Running"
	# print("{} set status of {} to Running".format(caller, service))

# update status
def updateStatus():
	global processes
	for service in processes:
		## TODO: marks as not running after stop-all and start-all
		try:
			if processes[service]["process"].poll() is not None:
				setServiceNotRunning(service, "updateStatus()::try")
		except Exception as e:
			setServiceNotRunning(service, "updateStatus()::except::" + str(e))


# helper function to run a command
def runCommand(cmd):
	# return subprocess.Popen("exec " + cmd, shell=True, stdout=logfile, stderr=logfile)
	return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
	# return subprocess.Popen(cmd.strip().split(), shell=False, stdout=logfile, stderr=logfile)

# runs server
def startServer():
	server = HTTPServer(('', port), Handler)
	server.serve_forever()



# start all the processes
startProcesses()


# initialize a mqtt client
mqtt = helper.MQTT(client_id="jarvis.py")
mqtt.on_message(handler)
mqtt.subscribe("jarvis/#")


# starts the http server
server_process = multiprocessing.Process(target=startServer)
server_process.start()


# register signal handlers
signal.signal(signal.SIGINT, stopProcesses)
signal.signal(signal.SIGTERM, stopProcesses)



# mainloop
# i = 0
while 1:
	try:
		time.sleep(1)
		# if i % 50000 == 0:
		# 	updateStatus()
		# 	i = 0
	
		# i += 1
		updateStatus()
	except KeyboardInterrupt:
		stopProcesses()
		pass
	except ProcessLookupError:
		pass