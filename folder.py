#!/usr/bin/python

class Folder:
    def __init__(self, file):
        self._file = file
        self._files = {}
        self._folders = {}

    @property
    def file(self):
        return self._file

    @property
    def folders(self):
        return self._folders

    def addChild(self, file):
        if file.folder:
            self._folders[file.name] = file
        else:
            self._files[file.name] = file
