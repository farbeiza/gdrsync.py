#!/usr/bin/python

import remotefile
import remotefolder
import virtualfolder

class Factory(virtualfolder.Factory):
    def __init__(self, drive):
        self._folderFactory = remotefolder.Factory(drive)
        self._fileFactory = remotefile.Factory(drive)

    @property
    def folderFactory(self):
        return self._folderFactory

    @property
    def fileFactory(self):
        return self._fileFactory
