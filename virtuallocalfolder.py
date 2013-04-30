#!/usr/bin/python

import folder
import localfile
import localfolder
import virtualfile

import os

def create(localPaths):
    localFolderFactory = localfolder.Factory()
    localFileFactory = localfile.Factory()

    virtualFolder = folder.Folder(virtualfile.VirtualFile(True))
    for localPath in localPaths:
        (head, tail) = os.path.split(localPath)
        if tail == '':
            localFolder = localFolderFactory.create(head)
            virtualFolder.addChildren(localFolder.children.values())
        else:
            localFile = localFileFactory.create(localPath)
            virtualFolder.addChild(localFile)

    return virtualFolder
