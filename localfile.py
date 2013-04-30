#!/usr/bin/python

import file
import utils

import date
import hashlib
import os

MD5_BUFFER_SIZE = 16 * utils.KIB

def fromParent(parent, path):
    return fromParentPath(parent.path, path)

def fromParentPath(parentPath, path):
    path = os.path.join(parentPath, os.path.basename(path))

    return LocalFile(path)

class LocalFile(file.File):
    def __init__(self, path, folder = None):
        path = unicode(path)
        name = os.path.basename(path)
        folder = utils.firstNonNone(folder, os.path.isdir(path))

        super(LocalFile, self).__init__(path, name, folder)

    @property
    def delegate(self):
        return self.path

    @property
    def contentSize(self):
        return os.path.getsize(self.path)

    @property
    def modified(self):
        return date.fromSeconds(os.path.getmtime(self.path))

    @property
    def contentMd5(self):
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
