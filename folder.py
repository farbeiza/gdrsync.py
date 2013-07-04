#!/usr/bin/python

import file
import utils

import os

class Folder(object):
    def __init__(self, file, children = None, duplicate = None):
        # Never instantiate the base class.
        assert self.__class__ != Folder
        self._file = file
        self._children = utils.firstNonNone(children, {})
        self._duplicate = utils.firstNonNone(duplicate, [])

    def _newFolder(self, file, children = None, duplicate = None):
        return self.__class__(file, children, duplicate)

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
        return self._newFolder(self._file)

    def withoutDuplicate(self):
        return self._newFolder(self._file, self._children)

    def createFile(self, name, folder = None):
        raise NotImplementedError()
