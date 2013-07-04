#!/usr/bin/python

import localfile
import localfolder
import virtualfolder

import os

class Factory(virtualfolder.Factory):
    def __init__(self, context):
        self._folderFactory = localfolder.Factory(context)
        self._fileFactory = localfile.Factory(context)

    def split(self, path):
        return os.path.split(path)

    @property
    def folderFactory(self):
        return self._folderFactory

    @property
    def fileFactory(self):
        return self._fileFactory
