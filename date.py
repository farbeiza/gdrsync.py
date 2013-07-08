#!/usr/bin/python

import calendar
import datetime
import functools

MS = 1000 # milliseconds / second
US = MS * MS # microseconds / second

# Time resolution in Google Drive is milliseconds
SCALE = 3
PRECISION = 10 ** SCALE

DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

# INVALID_SECONDS is a special value used in Google Drive for empty Dates
INVALID_SECONDS = 0.0
SUBSTITUTE_SECONDS = float(1) / PRECISION

def fromSeconds(seconds):
    return Date(seconds)

def fromString(string):
    dateTime = datetime.datetime.strptime(string, DATE_TIME_FORMAT)
    seconds = (calendar.timegm(dateTime.timetuple())
            + (float(dateTime.microsecond) / US))
    if seconds == SUBSTITUTE_SECONDS:
        seconds = INVALID_SECONDS

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
        seconds = self._seconds
        if seconds == INVALID_SECONDS:
            seconds = SUBSTITUTE_SECONDS

        dateTime = datetime.datetime.utcfromtimestamp(seconds)

        return dateTime.strftime(DATE_TIME_FORMAT)

    @property
    def seconds(self):
        return self._seconds
