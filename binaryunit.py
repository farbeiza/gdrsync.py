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

import utils

BASE = float(utils.KIB)
MAX_NUMBER = 10000.0
PREFIXES = ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi']

def bS(bytes, time):
    if round(time) == 0:
        return _bS(0)

    return _bS(bytes / time)

def _bS(value):
    return BinaryUnit(value, 'B/s')

class BinaryUnit(object):
    def __init__(self, value, unit):
        power = self.power(value)

        self._value = value / (BASE ** power)
        self._unit = PREFIXES[power] + unit

    def power(self, number):
        for power in range(len(PREFIXES)):
            if number < MAX_NUMBER:
                return power

            number /= BASE

        return len(PREFIXES) - 1

    @property
    def value(self):
        return self._value

    @property
    def unit(self):
        return self._unit
