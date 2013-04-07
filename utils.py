#!/usr/bin/python

KIB = 0x400 # bytes / kibibyte
MIB = KIB * KIB # bytes / mebibyte

MS = 1000 # milliseconds / second
US = MS * MS # microseconds / second

def firstNonNone(*arguments):
    for argument in arguments:
        if argument is not None:
            return argument

    raise RuntimeError('No non None argument')
