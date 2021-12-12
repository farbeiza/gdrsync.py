#!/usr/bin/python
#
# Copyright 2015 Fernando Arbeiza <fernando.arbeiza@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import configparser
import logging
import os

APPLICATION_NAME = 'gdrsync'
CONFIG_DIR = os.path.expanduser(os.path.join('~', '.config', APPLICATION_NAME))
CONFIG_FILE_NAME = 'config.ini'
CONFIG_FILE = os.path.join(CONFIG_DIR, CONFIG_FILE_NAME)

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
    os.makedirs(CONFIG_DIR, exist_ok=True)

    with open(CONFIG_FILE, 'w') as file:
        PARSER.write(file)
