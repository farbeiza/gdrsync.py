#!/usr/bin/python

import os

def fromParent(parent, path):
    return fromParentPath(parent.path, path)

def fromParentPath(parentPath, path):
    path = os.path.join(parentPath, os.path.basename(path))

    return File(path)

class File(object):
    def __init__(self, path):
        self._path = path

    @property
    def path(self):
        return self._path

    @property
    def exists(self):
        return False
