#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Fernando Arbeiza <fernando.arbeiza@gmail.com>
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

import argumentparser

ARGS = argumentparser.PARSER.parse_args()

import logging

LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]
LOG_LEVEL = LOG_LEVELS[min(ARGS.verbosity, len(LOG_LEVELS) - 1)]

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(name)s: %(message)s',
                    level=LOG_LEVEL)
if ARGS.verbosity < len(LOG_LEVELS):
    logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)

import sync

if __name__ == '__main__':
    sync_instance = sync.Sync(ARGS)
    sync_instance.sync()
    sync_instance.close()
