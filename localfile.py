#!/usr/bin/python

import hashlib
import os

MD5_BUFFER_SIZE = 16 * 1024

def fromParent(parent, path):
    return fromParentPath(parent.path, path)

def fromParentPath(parentPath, path):
    path = os.path.join(parentPath, os.path.basename(path))

    return LocalFile(path)

class LocalFile(object):
    def __init__(self, path):
        self._path = path

    @property
    def delegate(self):
        return self._path

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return os.path.basename(self._path)

    @property
    def size(self):
        return os.path.getsize(self._path)

    @property
    def modified(self):
        return round(os.path.getmtime(self._path))

    @property
    def md5(self):
        with open(self._path, mode = 'rb') as file:
            md5 = hashlib.md5()
            while True:
                data = file.read(MD5_BUFFER_SIZE)
                if not data:
                    break

                md5.update(data)

        return md5.hexdigest()

    @property
    def folder(self):
        return os.path.isdir(self._path)

class Factory(object):
    def create(self, path):
        if not os.path.exists(path):
            raise RuntimeError('%s not found' % path)

        return LocalFile(path)
