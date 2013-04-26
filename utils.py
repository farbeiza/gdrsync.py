#!/usr/bin/python

KIB = 0x400 # bytes / kibibyte
MIB = KIB * KIB # bytes / mebibyte

def firstNonNone(*arguments):
    for argument in arguments:
        if argument is not None:
            return argument

    raise RuntimeError('No non None argument')
