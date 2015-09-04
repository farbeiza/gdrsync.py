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

import calendar
import datetime
import functools
import math

MS = 1000 # milliseconds / second
US = MS * MS # microseconds / second

DATE_TIME_PARSE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

DATE_TIME_PRINT_FORMAT = '%Y-%m-%dT%H:%M:%S'
MILLIS_OF_SECOND_PRINT_FORMAT = '.%sZ'

# INVALID_MILLIS is a special value used in Google Drive for empty Dates
INVALID_MILLIS = 0
SUBSTITUTE_SECONDS = float(1) / MS

def fromSeconds(seconds):
    return Date(seconds * MS)

def fromString(string):
    dateTime = datetime.datetime.strptime(string, DATE_TIME_PARSE_FORMAT)
    seconds = (calendar.timegm(dateTime.timetuple())
            + (float(dateTime.microsecond) / US))
    if seconds == SUBSTITUTE_SECONDS:
        return invalidDate()

    return fromSeconds(seconds)

def invalidDate():
    return Date(INVALID_MILLIS)

@functools.total_ordering
class Date(object):
    def __init__(self, millis):
        # Time resolution in Google Drive is milliseconds
        self._millis = round(millis)

    @property
    def seconds(self):
        return float(self._millis) / MS

    def __eq__(self, other):
        return self._millis == other._millis

    def __lt__(self, other):
        return self._millis < other._millis

    def __hash__(self):
        return self._millis

    def __str__(self):
        seconds = self.seconds
        if self._millis == INVALID_MILLIS:
            seconds = SUBSTITUTE_SECONDS

        dateTime = datetime.datetime.utcfromtimestamp(seconds)

        # strftime does not have a format directive for milliseconds
        millisOfSecond = self._millis % MS

        return (dateTime.strftime(DATE_TIME_PRINT_FORMAT)
                + (MILLIS_OF_SECOND_PRINT_FORMAT % millisOfSecond))
