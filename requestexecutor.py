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

import logging
import random
import time

RETRIES = 5

LOGGER = logging.getLogger(__name__)


def execute(request, retries=RETRIES):
    retry = 0
    while True:
        try:
            return request()
        except BaseException as exception:
            if retry >= retries:
                raise exception

            wait = exponentialBackoffWait(retry)
            LOGGER.exception('Retry %d failed. Retrying after %f s...', retry, wait)

            time.sleep(wait)
            retry += 1


def exponentialBackoffWait(retry):
    return (2 ** retry) + random.random()
