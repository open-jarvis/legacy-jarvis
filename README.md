# Jarvis
just another rather very intelligent system


---


## Hardware/Software used
- [ReSpeaker 4-Mic Array](#mic)
- [Snowboy (hotword)](#snowboy)
- [PocketSphinx (speech-to-text)](#pocketsphinx)



<br>


## Installation


<h3 id="mic">ReSpeaker 4-Mic Array</h3>

> Installation instructions can be found here:  
> https://wiki.seeedstudio.com/ReSpeaker_4_Mic_Array_for_Raspberry_Pi/

#### Install the Audio drivers
```bash
sudo apt update -y
sudo apt upgrade -y
git clone https://github.com/respeaker/seeed-voicecard.git
cd seeed-voicecard
sudo ./install.sh
reboot
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

#### Install python packages
```bash
pip install webrtcvad # for voice activity detection
```

#### Test the setup
```bash
arecord -Dac108 -f S32_LE -r 16000 -c 4 hello.wav
aplay hello.wav
```

<br>

<h3 id="snowboy">Snowboy</h3>

> If the installation fails, check out http://docs.kitt.ai/snowboy/ (shut down on 31st Dec 2020) or https://github.com/f1ps1/snowboy  (backup of the original repository) for instructions!

#### Installing dependencies
```bash
sudo apt-get install -y python-pip python3-pip python-pyaudio python3-pyaudio sox swig libatlas-base-dev gcc g++ make wget
pip install pyaudio
pip3 install pyaudio
```

#### Compiling Snowboy
```bash
cd <jarvis-installation-path>/lib
git clone https://github.com/f1ps1/snowboy
cd snowboy
sudo python3 setup.py install
cd swig/Python3
make
```

<br>

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
sudo apt install -y bison libasound2-dev swig

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