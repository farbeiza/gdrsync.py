#!/usr/bin/python

import file
import folder
import localfile

import os
import urllib.parse

SCHEME = 'file'

class LocalFolder(folder.Folder):
    def withoutChildren(self):
        return LocalFolder(self._file)

    def withoutDuplicate(self):
        return LocalFolder(self._file, self._children)

    def createFile(self, name, folder = None):
        return localfile.fromParent(self.file, name, folder)

class Factory(folder.Factory):
    def isRemote(self):
        return False

    def handlesUrl(self, url):
        return True

    def empty(self, file):
        return LocalFolder(file)

    def pathFromUrl(self, urlString):
        url = urllib.parse.urlparse(urlString)
        if url.scheme != SCHEME:
            return urlString

        return url.path

    def create(self, file):
        if not isinstance(file, localfile.LocalFile):
            localFileFactory = localfile.Factory()

            return self.create(localFileFactory.create(file))

        localFolder = LocalFolder(file)
        for path in os.listdir(file.delegate):
            localFile = localfile.fromParent(file, path)
            localFolder.addChild(localFile)

        return localFolder

    def virtual(self):
        return self.empty(file.File(None, None))

    def split(self, path):
        return os.path.split(path)

    @property
    def fileFactory(self):
        return localfile.Factory()
