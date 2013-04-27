#!/usr/bin/python

import folder
import localfile
import localfolder
import virtualfile

import os

def create(localPaths):
    virtualFolder = folder.Folder(virtualfile.VirtualFile(True))
    for localPath in localPaths:
        (head, tail) = os.path.split(localPath)
        if tail == '':
            localFolder = localfolder.create(head)
            virtualFolder.addChildren(localFolder.children.values())
        else:
            virtualFolder.addChild(localfile.LocalFile(localPath))

    return virtualFolder
