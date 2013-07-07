#!/usr/bin/python
# -*- coding: utf-8 -*-

class DriveMock:
    def __init__(self, iteration = 0, has_sub_iteration = True):
        self._iteration = iteration
        self._has_sub_iteration = has_sub_iteration

    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        if kwargs.get('maxResults', 0) > 1:
            return DriveMock(0, False)
        return self

    def __str__(self):
        return 'DriveMock(%d, %s)' % (self._iteration, self._has_sub_iteration)

    def __int__(self):
        return 1

    def __iter__(self):
        if not self._has_sub_iteration:
            return DriveMock(0, False)
        return DriveMock(1)

    def __nonzero__(self):
        return False

    def next(self):
        if self._iteration > 0:
            self._iteration -= 1
            return self
        raise StopIteration()

    def get(self, *args, **kwargs):
        if len(args) == 1 and args[0] == 'nextPageToken':
            return None
        return self
