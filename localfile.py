#!/usr/bin/python

import file
import utils

import hashlib
import math
import os

MD5_BUFFER_SIZE = 16 * 1024

def fromParent(parent, path):
    return fromParentPath(parent.path, path)

def fromParentPath(parentPath, path):
    path = os.path.join(parentPath, os.path.basename(path))

    return LocalFile(path)

class LocalFile(file.File):
    def __init__(self, path, folder = None):
        name = os.path.basename(path)
        folder = utils.firstNonNone(folder, os.path.isdir(path))

        super(LocalFile, self).__init__(path, name, folder)

    @property
    def delegate(self):
        return self.path

    @property
    def size(self):
        return os.path.getsize(self.path)

    @property
    def modified(self):
        # Milliseconds in modified time are not supported in all
        # systems/languages
        return math.floor(os.path.getmtime(self.path))

    @property
    def md5(self):
        with open(self.path, mode = 'rb') as file:
            md5 = hashlib.md5()
            while True:
                data = file.read(MD5_BUFFER_SIZE)
                if not data:
                    break

                md5.update(data)

        return md5.hexdigest()

    @property
    def exists(self):
        return os.path.exists(self.path)

class Factory(object):
    def create(self, path):
        if not os.path.exists(path):
            raise RuntimeError('%s not found' % path)

        return LocalFile(path)
