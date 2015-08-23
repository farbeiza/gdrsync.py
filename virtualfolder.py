#!/usr/bin/python

import folder
import virtualfile

import os

class Factory(object):
    def create(self, paths):
        virtualFolder = folder.Folder(virtualfile.VirtualFile(True))
        for path in paths:
            (head, tail) = self.split(path)
            if tail == '':
                pathFolder = self.folderFactory.create(head)
                virtualFolder.addChildren(list(pathFolder.children.values()))
            else:
                pathFile = self.fileFactory.create(path)
                virtualFolder.addChild(pathFile)

        return virtualFolder

    def split(self, path):
        raise NotImplementedError()

    @property
    def folderFactory(self):
        raise NotImplementedError()

    @property
    def fileFactory(self):
        raise NotImplementedError()
