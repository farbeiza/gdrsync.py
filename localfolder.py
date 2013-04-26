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
            localFile = localfile.fromParent(file, path)
            localFolder.addChild(localFile)

        return localFolder
