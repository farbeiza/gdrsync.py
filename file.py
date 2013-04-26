#!/usr/bin/python

import utils

import math
import hashlib
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
    def size(self):
        if self.folder:
            return 0

        return self.contentSize

    @property
    def contentSize(self):
        raise NotImplementedError()

    @property
    def modified(self):
        # Milliseconds in modified time are not supported in all systems
        return math.floor(self.modifiedImpl)

    @property
    def modifiedImpl(self):
        raise NotImplementedError()

    @property
    def md5(self):
        if self.folder:
            md5 = hashlib.md5()
            md5.update(self.name)

            return md5.hexdigest()

        return self.contentMd5

    @property
    def contentMd5(self):
        raise NotImplementedError()

    @property
    def exists(self):
        return False
