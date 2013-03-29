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

class GDRsync(object):
    def __init__(self):
        self.localFolderFactory = localfolder.Factory()
        self.remoteFolderFactory = remotefolder.Factory()

    def sync(self, localPath, remotePath):
        LOGGER.info('Starting...')

        self._sync(self.localFolderFactory.create(localPath),
                self.remoteFolderFactory.create(remotePath))

        LOGGER.info('End.')

    def _sync(self, localFolder, remoteFolder):
        remoteFolder = self.trash(localFolder, remoteFolder)

        remoteFolder = self.insertFolders(localFolder, remoteFolder)

        for localFile in localFolder.folders():
            remoteFile = remoteFolder.children[localFile.name]

            childLocalFolder = self.localFolderFactory.create(localFile)
            childRemoteFolder = self.remoteFolderFactory.create(remoteFile)

            self._sync(childLocalFolder, childRemoteFolder)

    def trash(self, localFolder, remoteFolder):
        remoteFolder = self.trashExtraneous(localFolder, remoteFolder)

        return remoteFolder

    def trashExtraneous(self, localFolder, remoteFolder):
        output = remotefolder.RemoteFolder(remoteFolder.file)
        for name, remoteFile in remoteFolder.children.iteritems():
            if remoteFile.name in localFolder.children:
                output.addChild(remoteFile)
                continue

            LOGGER.debug('%s: Extraneous file...', remoteFile.path)

            remoteFile = self.trashFile(remoteFile)

        return output

    def trashFile(self, remoteFile):
        LOGGER.info('%s: Trashing file...', remoteFile.path)

        def request():
            return (driveutils.DRIVE.files()
                    .trash(fileId = remoteFile.delegate['id'],
                            fields = driveutils.FIELDS)
                    .execute())

        file = requestexecutor.execute(request)

        return remoteFile.withDelegate(file)

    def insertFolders(self, localFolder, remoteFolder):
        output = remotefolder.RemoteFolder(remoteFolder.file)
        output.addChildren(remoteFolder.children.values())

        for localFile in localFolder.folders():
            remoteFile = remoteFolder.children.get(localFile.name)
            if remoteFile is not None:
                LOGGER.debug('%s: Existing folder.', remoteFile.path)
                continue

            remoteFile = remoteFolder.createRemoteFile(localFile.name, 
                    driveutils.MIME_FOLDER)
            remoteFile = self.insertFolder(localFile, remoteFile)

            output.addChild(remoteFile)

        return output

    def insertFolder(self, localFile, remoteFile):
        LOGGER.info('%s: Inserting folder...', remoteFile.path)

        def request():
            return (driveutils.DRIVE.files().insert(body = remoteFile.delegate,
                    fields = driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return remoteFile.withDelegate(file)

GDRsync().sync(sys.argv[1], sys.argv[2])
