#!/usr/bin/python

import file
import folder
import localfile

import os

class LocalFolder(folder.Folder):
    def createFile(self, name, folder = None):
        return localfile.fromParent(self.file, name, folder)

class Factory(object):
    def __init__(self, context):
        self.localFileFactory = localfile.Factory(context)
        self.context = context

    def createEmpty(self, file):
        return LocalFolder(file)

    def create(self, fileinstance):
        if not isinstance(fileinstance, file.File):
            return self.create(
                self.localFileFactory.create(self.context, fileinstance))

        localFolder = LocalFolder(fileinstance)
        for path in os.listdir(fileinstance.path):
            localFile = localfile.fromParent(fileinstance, path)
            localFolder.addChild(localFile)

        return localFolder
