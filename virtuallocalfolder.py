#!/usr/bin/python

import localfile
import localfolder
import virtualfolder

class Factory(virtualfolder.Factory):
    def __init__(self):
        self._folderFactory = localfolder.Factory()
        self._fileFactory = localfile.Factory()

    @property
    def folderFactory(self):
        return self._folderFactory

    @property
    def fileFactory(self):
        return self._fileFactory
