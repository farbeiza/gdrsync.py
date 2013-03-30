#!/usr/bin/python

def firstNonNone(*arguments):
    for argument in arguments:
        if argument is not None:
            return argument

    raise RuntimeError('No non None argument')
