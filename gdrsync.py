#!/usr/bin/python

import config

import logging

logging.basicConfig()
logging.getLogger().setLevel(config.PARSER.get('gdrsync', 'logLevel'))

import localfolder
import remotefolder

import sys

LOGGER = logging.getLogger(__name__)

class GDRsync:
    def __init__(self):
        self.localFolderFactory = localfolder.Factory()
        self.remoteFolderFactory = remotefolder.Factory()

    def sync(self, localPath, remotePath):
        LOGGER.info('Starting...')

        self._sync(self.localFolderFactory.create(localPath),
                self.remoteFolderFactory.create(remotePath))

        LOGGER.info('End.')

    def _sync(self, localFolder, remoteFolder):
        for name, localFile in localFolder.folders.iteritems():
            remoteFile = remoteFolder.folders[localFile.name]

            childLocalFolder = self.localFolderFactory.create(localFile)
            childRemoteFolder = self.remoteFolderFactory.create(localFile)

            self._sync(childLocalFolder, childRemoteFolder)

GDRsync().sync(sys.argv[1], sys.argv[2])
