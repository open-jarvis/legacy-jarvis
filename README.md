# Jarvis
"just another rather very intelligent system"  
Jarvis is an open-source AI-based extendable home assistant



## Hardware/Software used
- [Downloading the Jarvis Code](#jarvis)
- [Packages to Install](#packages)
- [ReSpeaker 4-Mic Array](#mic)
- [Snowboy (hotword)](#snowboy)
- [PocketSphinx (speech-to-text)](#pocketsphinx)
- [Snips-NLU (language understanding)](#snips-nlu)



## Installation


<h3 id="jarvis">Downloading the Jarvis Code</h3>

First, you'll need to create a folder to install Jarvis in. You can use any directory, but make sure it's readable and writeable.

```bash
sudo mkdir /jarvis
sudo chown pi:pi /jarvis
git clone https://github.com/open-jarvis/jarvis /jarvis
```




<h3 id="packages">Packages to install</h3>

```bash
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y git python3 python3-pip mosquitto
pip3 install paho-mqtt gpiozero spidev psutil
```


<h3 id="mic">ReSpeaker 4-Mic Array</h3>

> Installation instructions can be found here:  
> https://wiki.seeedstudio.com/ReSpeaker_4_Mic_Array_for_Raspberry_Pi/

#### Install the Audio drivers
```bash
sudo apt update -y
sudo apt upgrade -y
sudo apt install git -y
git clone https://github.com/respeaker/seeed-voicecard.git
cd seeed-voicecard --compat-kernel
sudo ./install.sh
sudo reboot
```

#### Change the audio output to 3.5mm jack
```bash
sudo raspi-config
# Select 7 Advanced Options
# Select A4 Audio
# Select 1 Force 3.5mm ('headphone') jack
# Select Finish
```

#### Activate the LED programmable interface
```bash
sudo raspi-config
# Go to "Interfacing Options"
# Go to "SPI"
# Enable SPI
# Exit the tool
```

#### Test the setup
```bash
arecord -Dac108 -f S32_LE -r 16000 -c 4 hello.wav
aplay hello.wav
```



<h3 id="snowboy">Snowboy</h3>

> If the installation fails, check out http://docs.kitt.ai/snowboy/ (shut down on 31st Dec 2020) or https://github.com/f1ps1/snowboy  (backup of the original repository) for instructions!

#### Installing dependencies
```bash
sudo apt-get install -y python-pip python3-pip python-pyaudio python3-pyaudio sox swig libatlas-base-dev gcc g++ make wget pulseaudio
pip install pyaudio webrtcvad
pip3 install pyaudio webrtcvad
```

#### Compiling Snowboy
```bash
cd <jarvis-installation-path>/engine/lib	# <jarvis-installation-path> should be /jarvis
git clone https://github.com/open-jarvis/snowboy
cd snowboy
sudo python3 setup.py install
cd swig/Python3
make
```



<h3 id="pocketsphinx">PocketSphinx</h3>

> Installation instructions are available here:  
> https://howchoo.com/g/ztbhyzfknze/how-to-install-pocketsphinx-on-a-raspberry-pi

#### Downloading CMUSphinx and PocketSphinx
```bash
wget https://sourceforge.net/projects/cmusphinx/files/sphinxbase/5prealpha/sphinxbase-5prealpha.tar.gz/download -O sphinxbase.tar.gz
wget https://sourceforge.net/projects/cmusphinx/files/pocketsphinx/5prealpha/pocketsphinx-5prealpha.tar.gz/download -O pocketsphinx.tar.gz

tar -xzvf sphinxbase.tar.gz
tar -xzvf pocketsphinx.tar.gz
```

#### Compiling CMUSphinx and PocketSphinx
```bash
sudo apt install -y bison libasound2-dev libpulse-dev swig

cd sphinxbase-5prealpha
./configure --enable-fixed
make
sudo make install

cd ../pocketsphinx-5prealpha
./configure
make
sudo make install
```

#### Install PocketSphinx for Python
```bash
pip3 install pocketsphinx
# pocketsphinx is available as a module now:
# import pocketsphinx
```

<br>

<h3 id="snips-nlu">Snips-NLU</h3>

#### Installing Snips-NLU and a language pack

[Instructions](https://github.com/snipsco/snips-issues/issues/161#issuecomment-508520769)

```bash
sudo apt install -y libatlas3-base=3.10.3-8+rpi1 libgfortran5
cd /home/pi
wget --content-disposition https://github.com/jr-k/snips-nlu-rebirth/blob/master/wheels/scipy-1.3.3-cp37-cp37m-linux_armv7l.whl?raw=true
wget --content-disposition https://github.com/jr-k/snips-nlu-rebirth/blob/master/wheels/scikit_learn-0.22.1-cp37-cp37m-linux_armv7l.whl?raw=true
wget --content-disposition https://github.com/jr-k/snips-nlu-rebirth/blob/master/wheels/snips_nlu_utils-0.9.1-cp37-cp37m-linux_armv7l.whl?raw=true
wget --content-disposition https://github.com/jr-k/snips-nlu-rebirth/blob/master/wheels/snips_nlu_parsers-0.4.3-cp37-cp37m-linux_armv7l.whl?raw=true
wget --content-disposition https://github.com/jr-k/snips-nlu-rebirth/blob/master/wheels/snips_nlu-0.20.2-py3-none-any.whl?raw=true

sudo pip3 install scipy-1.3.3-cp37-cp37m-linux_armv7l.whl
sudo pip3 install scikit_learn-0.22.1-cp37-cp37m-linux_armv7l.whl
sudo pip3 install snips_nlu_utils-0.9.1-cp37-cp37m-linux_armv7l.whl
sudo pip3 install snips_nlu_parsers-0.4.3-cp37-cp37m-linux_armv7l.whl
sudo pip3 install snips_nlu-0.20.2-py3-none-any.whl

sudo python3 -m snips_nlu download de
```



#### Creating a dataset
In order to use the Snips-NLU engine we have to create a sample dataset. This dataset should look like the following:
```json
{
	"entities": {
		"color": {
			"automatically_extensible": true,
			"data": [],
			"matching_strictness": 1,
			"use_synonyms": true 
		},
		"room": {
			"automatically_extensible": true,
			"data": [
				{
					"value": "garden",
					"synonyms": []
				},
				{
					"value": "garage",
					"synonyms": []
				}
			],
			"matching_strictness": 1,
			"use_synonyms": true 
		}
	},
	"intents": {
		"turn_lights_on": {
			"utterances": [
				{
					"data": [
						{ "text": "turn on the lights in the " },
						{
							"entity": "room",
							"slot_name": "room",
							"text": "kitchen"
						}
					]
				}
			]
		}
	},
	"language": "en"
}
```
After the dataset is finished, we can let Snips-NLU train it:
```bash
snips-nlu train dataset.json output_model
```