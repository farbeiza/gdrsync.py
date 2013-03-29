#!/usr/bin/python

import folder
import localfile

import os

class Factory(object):
    def create(self, file):
        if not isinstance(file, localfile.LocalFile):
            return self.create(localfile.Factory().create(file))

        localFolder = folder.Folder(file)
        for path in os.listdir(file.delegate):
            localFolder.addChild(localfile.fromParent(file, path))

        return localFolder
