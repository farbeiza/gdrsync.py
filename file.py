#!/usr/bin/python

import utils

import os

def fromParent(parent, path, folder = None):
    return fromParentPath(parent.path, path, folder)

def fromParentPath(parentPath, path, folder = None):
    name = os.path.basename(path)
    path = os.path.join(parentPath, name)

    return File(path, name, folder)

class File(object):
    def __init__(self, path, name, folder = None):
        self._path = path
        self._name = name
        self._folder = utils.firstNonNone(folder, False)

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    @property
    def folder(self):
        return self._folder

    @property
    def exists(self):
        return False
