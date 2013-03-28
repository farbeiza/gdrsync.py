#!/usr/bin/python

import folder
import localfile

import os

class Factory:
    def create(self, file):
        if not isinstance(file, localfile.LocalFile):
            return self.create(localfile.LocalFile(file))

        localFolder = folder.Folder(file)
        for path in os.listdir(file.delegate):
            localFolder.addChild(localfile.LocalFile(path))

        return localFolder
