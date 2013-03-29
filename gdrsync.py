#!/usr/bin/python

import config

import logging

logging.basicConfig()
logging.getLogger().setLevel(config.PARSER.get('gdrsync', 'logLevel'))

import driveutils
import localfolder
import remotefolder
import requestexecutor

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
        self.syncFolders(localFolder, remoteFolder)

        for name, localFile in localFolder.folders.iteritems():
            remoteFile = remoteFolder.folders[localFile.name]

            childLocalFolder = self.localFolderFactory.create(localFile)
            childRemoteFolder = self.remoteFolderFactory.create(localFile)

            self._sync(childLocalFolder, childRemoteFolder)

    def syncFolders(self, localFolder, remoteFolder):
        self.insertFolders(localFolder, remoteFolder)
        self.trashFolders(localFolder, remoteFolder)

    def insertFolders(self, localFolder, remoteFolder):
        for name, localFile in localFolder.folders.iteritems():
            remoteFile = remoteFolder.folders.get([localFile.name])
            if remoteFile is not None:
                LOGGER.debug('%s: Existing folder.', remoteFile.path)
                continue

            remoteFile = remoteFolder.newRemoteFile(localFile.name, 
                    driveutils.MIME_FOLDER)
            remoteFile = self.insertFolder(localFile, remoteFile)

            remoteFolder.folders[remoteFile.name] = remoteFile

    def insertFolder(self, localFile, remoteFile):
        LOGGER.info('%s: Inserting folder...', remoteFile.path)

        def request():
            return (driveutils.DRIVE.files().insert(body = remoteFile.delegate,
                    fields = driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return remoteFile.withDelegate(file)

    def trashFolders(self, localFolder, remoteFolder):
        for name, remoteFile in remoteFolder.folders.items():
            localFile = localFolder.folders.get(remoteFile.name)
            if localFile is not None:
                continue

            remoteFile = self.trashFolder(remoteFile)

            del remoteFolder.folders[remoteFile.name]

    def trashFolder(self, remoteFile):
        LOGGER.info('%s: Trashing folder...', remoteFile.path)

        def request():
            return (driveutils.DRIVE.files()
                    .trash(fileId = remoteFile.delegate['id'],
                            fields = driveutils.FIELDS)
                    .execute())

        file = requestexecutor.execute(request)

        return remoteFile.withDelegate(file)

GDRsync().sync(sys.argv[1], sys.argv[2])
