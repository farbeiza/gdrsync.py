#!/usr/bin/python

import file
import utils

import os.path

def empty(file):
    return Folder(file)

class Folder(object):
    def __init__(self, file, children = None, duplicate = None):
        self._file = file
        self._children = utils.firstNonNone(children, {})
        self._duplicate = utils.firstNonNone(duplicate, [])

    def addChild(self, file):
        if file.name in self._children:
            self._duplicate.append(file)

            return self

        self._children[file.name] = file

        return self

    def addChildren(self, files):
        for file in files:
            self.addChild(file)

        return self

    @property
    def file(self):
        return self._file

    @property
    def children(self):
        return self._children

    @property
    def duplicate(self):
        return self._duplicate

    def files(self):
        return [child for child in self._children.values() if not child.folder]

    def folders(self):
        return [child for child in self._children.values() if child.folder]

    def withoutChildren(self):
        return Folder(self._file)

    def withoutDuplicate(self):
        return Folder(self._file, self._children)

    def createFile(self, name, folder = None):
        path = os.path.join(self._file.path, name)

        return file.File(path, name, folder)

class Factory(object):
    def fromUrl(self, url):
        return self.create(self.pathFromUrl(url))

    def pathFromUrl(self, url):
        raise NotImplementedError()

    def create(self, path):
        raise NotImplementedError()

    def virtualFromUrls(self, urls):
        return self.virtual([self.pathFromUrl(url) for url in urls])

    def virtual(self, paths):
        virtualFolder = Folder(file.VirtualFile(True))
        for path in paths:
            (head, tail) = self.split(path)
            if tail == '':
                pathFolder = self.create(head)
                virtualFolder.addChildren(pathFolder.children.values())
            else:
                pathFile = self.fileFactory.create(path)
                virtualFolder.addChild(pathFile)

        return virtualFolder

    def split(self, path):
        raise NotImplementedError()

    @property
    def fileFactory(self):
        raise NotImplementedError()
