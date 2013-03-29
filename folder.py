#!/usr/bin/python

class Folder(object):
    def __init__(self, file):
        self._file = file
        self._children = {}
        self._duplicate = []

    @property
    def file(self):
        return self._file

    @property
    def children(self):
        return self._children

    @property
    def duplicate(self):
        return self._duplicate

    def addChild(self, file):
        name = file.name
        if name in self._children:
            self._duplicate.append(file)

            return

        self._children[name] = file

    def addChildren(self, files):
        for file in files:
            self.addChild(file)

    def files(self):
        return filter(lambda f: not f.folder, self._children.values())

    def folders(self):
        return filter(lambda f: f.folder, self._children.values())
