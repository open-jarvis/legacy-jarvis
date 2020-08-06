#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: nlp.py [-h] [--config CONFIG]
# 
# Natural language processing engine using spaCy
# Convert spoken language into a command (skill) and arguments
# 
# optional arguments:
#   -h, --help       show this help message and exit
#   --config CONFIG  Path to jarvis configuration file


## input: jarvis/stt -> command:[words]
## output: jarvis/nlp -> skill:[skill]:arguments[arguments]


## import global packages
import os, sys, argparse


## import local packages
import spacy


## add a description and parse arguments
parser = argparse.ArgumentParser(description="Natural language processing engine using spaCy\nConvert spoken language into a command (skill) and arguments", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--config", type=str, help="Path to jarvis configuration file", default="../jarvis.conf")
args = parser.parse_args()


## get the config file from argparse and read it
config = configparser.ConfigParser()
config.read(args.config)
config = config["nlp"]


# initialize nlp instance
nlp = spacy.load(config["model"])