#!/usr/bin/python

import utils

BASE = float(utils.KIB)
MAX_NUMBER = 10000.0
PREFIXES = ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi']

class BinaryUnit(object):
    def __init__(self, value, unit):
        power = self.power(value)

        self._value = value / (BASE ** power)
        self._unit = PREFIXES[power] + unit

    def power(self, number):
        for power in range(len(PREFIXES)):
            if number < MAX_NUMBER:
                return power;

            number /= BASE

        return len(PREFIXES) - 1

    @property
    def value(self):
        return self._value

    @property
    def unit(self):
        return self._unit
