#!/usr/bin/python

import configparser
import logging
import os

APPLICATION_NAME = 'gdrsync.py'
CONFIG_FILE_NAME = '.' + APPLICATION_NAME
CONFIG_FILE = os.path.expanduser(os.path.join('~', CONFIG_FILE_NAME))

PARSER = configparser.SafeConfigParser()
PARSER.read(CONFIG_FILE)

SECTION = 'gdrsync'

LOGGER = logging.getLogger(__name__)

def get(option):
    if not PARSER.has_option(SECTION, option):
        return None

    return PARSER.get(SECTION, option)

def set(option, value):
    if not PARSER.has_section(SECTION):
        PARSER.add_section(SECTION)

    PARSER.set(SECTION, option, value)

def save():
    LOGGER.info('Saving config file %s...', CONFIG_FILE)
    with open(CONFIG_FILE, 'w') as file:
        PARSER.write(file)
