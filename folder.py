#!/usr/bin/python

import file
import utils

import os

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
        return filter(lambda f: not f.folder, self._children.values())

    def folders(self):
        return filter(lambda f: f.folder, self._children.values())

    def withoutChildren(self):
        return Folder(self._file)

    def withoutDuplicate(self):
        return Folder(self._file, self._children)

    def createFile(self, name, folder = None):
        path = os.path.join(self._file.path, name)
        
        return file.File(path, name, folder)
