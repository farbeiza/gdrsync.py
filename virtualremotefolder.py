#!/usr/bin/python

import remotefile
import remotefolder
import virtualfolder

import posixpath

class Factory(virtualfolder.Factory):
    def __init__(self, drive):
        self._folderFactory = remotefolder.Factory(drive)
        self._fileFactory = remotefile.Factory(drive)

    def split(self, path):
        return posixpath.split(path)

    @property
    def folderFactory(self):
        return self._folderFactory

    @property
    def fileFactory(self):
        return self._fileFactory
