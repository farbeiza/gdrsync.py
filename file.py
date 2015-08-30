#!/usr/bin/python

import utils

import hashlib

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
    def md5(self):
        if self.folder:
            md5 = hashlib.md5()
            md5.update(self.name.encode('utf-8'))

            return md5.hexdigest()

        return self.contentMd5

    @property
    def contentMd5(self):
        raise NotImplementedError()

    @property
    def exists(self):
        return False

class VirtualFile(File):
    def __init__(self, folder = None):
        super(VirtualFile, self).__init__(None, None, folder)
