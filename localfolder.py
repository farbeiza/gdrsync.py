#!/usr/bin/python

import folder
import localfile

import os

def create(file):
    if not isinstance(file, localfile.LocalFile):
        return create(localfile.create(file))

    localFolder = folder.Folder(file)
    for path in os.listdir(file.delegate):
        localFile = localfile.fromParent(file, path)
        localFolder.addChild(localFile)

    return localFolder
