#!/usr/bin/python

class TransferManager(object):
    def insertFolder(self, destinationFile):
        raise NotImplementedError()

    def insertFile(self, sourceFile, destinationFile):
        raise NotImplementedError()

    def updateFile(self, sourceFile, destinationFile):
        raise NotImplementedError()

    def remove(self, destinationFile):
        raise NotImplementedError()

    def touch(self, sourceFile, destinationFile):
        raise NotImplementedError()
