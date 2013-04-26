#!/usr/bin/python

import calendar
import datetime
import functools

MS = 1000 # milliseconds / second
US = MS * MS # microseconds / second

DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

# Time resolution in Google Drive is milliseconds
SCALE = 3
PRECISION = 10 ** SCALE

def fromSeconds(seconds):
    return Date(seconds)

def fromString(string):
    dateTime = datetime.datetime.strptime(string, DATE_TIME_FORMAT)
    seconds = (calendar.timegm(dateTime.timetuple())
            + (float(dateTime.microsecond) / US))

    return fromSeconds(seconds)

@functools.total_ordering
class Date(object):
    def __init__(self, seconds):
        self._seconds = round(seconds, SCALE)

    def __eq__(self, other):
        return self._seconds == other._seconds

    def __lt__(self, other):
        return self._seconds < other._seconds

    def __hash__(self):
        return round(self._seconds * PRECISION)

    def __str__(self):
        dateTime = datetime.datetime.utcfromtimestamp(self._seconds)

        return dateTime.strftime(DATE_TIME_FORMAT)
