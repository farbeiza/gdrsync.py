#!/usr/bin/python

import os

import ConfigParser

APPLICATION_NAME = "gdrsync.py"
CONFIG_FILE_NAME = "." + APPLICATION_NAME
CONFIG_FILE = os.path.expanduser(os.path.join('~', CONFIG_FILE_NAME))

PARSER = ConfigParser.SafeConfigParser()
PARSER.read(CONFIG_FILE)
