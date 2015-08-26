#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os

parser = argparse.ArgumentParser(description = 'Copy files from a local system'
        ' to a Google drive repository.')

parser.add_argument('localPaths', nargs='+',
        help = ('local paths. A trailing %s means "copy the contents of this'
                ' directory", as opposed to "copy the directory itself"'
                % os.path.sep),
        metavar = 'LOCAL')
parser.add_argument('remotePath', help = 'remote path', metavar = 'REMOTE')

parser.add_argument('-c', action = 'store_true',
        help = 'skip based on checksum, not mod-time & size', dest = 'checksum')
parser.add_argument('-d', action = 'store_true',
        help = 'delete duplicate and extraneous files from dest dirs',
        dest = 'delete')
parser.add_argument('-D', action = 'store_true',
        help = 'also delete excluded files from dest dirs',
        dest = 'deleteExcluded')
parser.add_argument('-e', action = 'append',
        help = 'exclude files matching PATTERN', metavar = 'PATTERN',
        dest = 'exclude')
parser.add_argument('-L', action = 'store_true',
        help = 'transform symlink into referent file/dir', dest = 'copyLinks')
parser.add_argument('-n', action = 'store_true',
        help = 'perform a trial run with no changes made', dest = 'dryRun')
parser.add_argument('-r', action = 'store_true',
        help = 'recurse into directories', dest = 'recursive')
parser.add_argument('-s', action = 'store_true',
        help = 'save credentials for future re-use', dest = 'saveCredentials')
parser.add_argument('-u', action = 'store_true',
        help = 'skip files that are newer on the receiver', dest = 'update')
parser.add_argument('-v', action='count', default = 0,
        help = 'increase verbosity', dest = 'verbosity')

args = parser.parse_args()

import logging

LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]
LOG_LEVEL = LOG_LEVELS[min(args.verbosity, len(LOG_LEVELS) - 1)]

logging.basicConfig(format = '%(asctime)s: %(levelname)s: %(name)s: %(message)s',
        level = LOG_LEVEL)
if args.verbosity < len(LOG_LEVELS):
    logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)
    logging.getLogger('oauth2client.client').setLevel(logging.ERROR)

import binaryunit
import driveutils
import folder
import localfolder
import remotefolder
import summary
import uploadmanager
import virtuallocalfolder

import errno
import re

LOGGER = logging.getLogger(__name__)

class GDRsync(object):
    def __init__(self, args):
        self.args = args

        self.exclude = []
        if self.args.exclude is not None:
            self.exclude = [re.compile(exclude) for exclude in self.args.exclude]

        drive = driveutils.drive(self.args.saveCredentials)

        self.localFolderFactory = localfolder.Factory()
        self.remoteFolderFactory = remotefolder.Factory(drive)

        self._summary = summary.Summary()

        self.transferManager = uploadmanager.UploadManager(drive, self._summary)

    def sync(self):
        LOGGER.info('Starting...')

        virtualLocalFolder = virtuallocalfolder.Factory().create(self.args.localPaths)
        remoteFolder = self.remoteFolderFactory.create(self.args.remotePath)
        self._sync(virtualLocalFolder, remoteFolder)

        self.logResult();

        LOGGER.info('End.')

    def _sync(self, localFolder, remoteFolder):
        remoteFolder = self.trash(localFolder, remoteFolder)

        self._summary.addTotalFiles(len(localFolder.children))

        remoteFolder = self.syncFolder(localFolder, remoteFolder)

        if not self.args.recursive:
            return

        for localFile in localFolder.folders():
            if self.isExcluded(localFile):
                LOGGER.info('%s: Skipping excluded folder...', localFile.path)
                continue

            if (not self.args.copyLinks) and localFile.link:
                continue

            remoteFile = remoteFolder.children[localFile.name]

            self._sync(self.createLocalFolder(localFile),
                    self.createRemoteFolder(remoteFile))

    def trash(self, localFolder, remoteFolder):
        remoteFolder = self.trashDuplicate(localFolder, remoteFolder)
        remoteFolder = self.trashExtraneous(localFolder, remoteFolder)
        remoteFolder = self.trashDifferentType(localFolder, remoteFolder)
        remoteFolder = self.trashExcluded(localFolder, remoteFolder)

        return remoteFolder

    def trashDuplicate(self, localFolder, remoteFolder):
        if not self.args.delete:
            return remoteFolder

        for remoteFile in remoteFolder.duplicate:
            LOGGER.debug('%s: Duplicate file.', remoteFile.path)

            remoteFile = self.trashFile(remoteFile)

        return remoteFolder.withoutDuplicate()

    def trashFile(self, remoteFile):
        LOGGER.info('%s: Trashing file...', remoteFile.path)
        if self.args.dryRun:
            return remoteFile

        return self.transferManager.remove(remoteFile)

    def trashExtraneous(self, localFolder, remoteFolder):
        if not self.args.delete:
            return remoteFolder

        output = remoteFolder.withoutChildren()
        for remoteFile in remoteFolder.children.values():
            if remoteFile.name in localFolder.children:
                output.addChild(remoteFile)
                continue

            LOGGER.debug('%s: Extraneous file.', remoteFile.path)

            remoteFile = self.trashFile(remoteFile)

        return output

    def trashDifferentType(self, localFolder, remoteFolder):
        if not self.args.delete:
            return remoteFolder

        output = remoteFolder.withoutChildren()
        for remoteFile in remoteFolder.children.values():
            localFile = localFolder.children[remoteFile.name]
            if localFile.folder == remoteFile.folder:
                output.addChild(remoteFile)
                continue

            LOGGER.debug('%s: Different type: %s != %s.', remoteFile.path,
                    localFile.folder, remoteFile.folder)

            remoteFile = self.trashFile(remoteFile)

        return output

    def trashExcluded(self, localFolder, remoteFolder):
        if not self.args.deleteExcluded:
            return remoteFolder

        output = remoteFolder.withoutChildren()
        for remoteFile in remoteFolder.children.values():
            localFile = localFolder.children[remoteFile.name]
            if not self.isExcluded(localFile):
                output.addChild(remoteFile)
                continue

            LOGGER.debug('%s: Excluded file.', remoteFile.path)

            remoteFile = self.trashFile(remoteFile)

        return output

    def isExcluded(self, localFile):
        if localFile.path is None:
            return False

        return any(re.match(localFile.path) for re in self.exclude)

    def syncFolder(self, localFolder, remoteFolder):
        output = (remoteFolder.withoutChildren()
                .addChildren(remoteFolder.children.values()))
        for localFile in localFolder.children.values():
            self._summary.addCheckedFiles(1)
            self._summary.addCheckedSize(localFile.size)

            try:
                remoteFile = self.copy(localFile, remoteFolder)
                if remoteFile is None:
                    continue

                output.addChild(remoteFile)
            except OSError as error:
                if error.errno != errno.ENOENT:
                    raise

                LOGGER.warn('%s: No such file or directory.', localFile.path)

        return output

    def copy(self, localFile, remoteFolder):
        remoteFile = remoteFolder.children.get(localFile.name)

        fileOperation = self.fileOperation(localFile, remoteFile)
        if fileOperation is None:
            return None

        if remoteFile is None:
            remoteFile = remoteFolder.createFile(localFile.name,
                    localFile.folder)

        return fileOperation(localFile, remoteFile)

    def fileOperation(self, localFile, remoteFile):
        if self.isExcluded(localFile):
            LOGGER.info('%s: Skipping excluded file... (Checked %d/%d files)',
                    localFile.path, self._summary.checkedFiles, self._summary.totalFiles)

            return None

        if (not self.args.copyLinks) and localFile.link:
            LOGGER.info('%s: Skipping non-regular file... (Checked %d/%d files)',
                    localFile.path, self._summary.checkedFiles, self._summary.totalFiles)

            return None

        if remoteFile is None:
            if localFile.folder:
                return self.insertFolder

            return self.insertFile

        if self.args.update and (remoteFile.modified > localFile.modified):
            LOGGER.debug('%s: Newer destination file: %s < %s.',
                    remoteFile.path, localFile.modified, remoteFile.modified)
        elif self.args.checksum:
            fileOperation = self.checkChecksum(localFile, remoteFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkSize(localFile, remoteFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkModified(localFile, remoteFile)
            if fileOperation is not None:
                return fileOperation
        else:
            fileOperation = self.checkSize(localFile, remoteFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkModified(localFile, remoteFile)
            if fileOperation is not None:
                return fileOperation

        LOGGER.debug('%s: Up to date. (Checked %d/%d files)', remoteFile.path,
                self._summary.checkedFiles, self._summary.totalFiles)

        return None

    def checkChecksum(self, localFile, remoteFile):
        if remoteFile.md5 == localFile.md5:
            return None

        LOGGER.debug('%s: Different checksum: %s != %s.', remoteFile.path,
                localFile.md5, remoteFile.md5)

        return self.updateFile

    def checkSize(self, localFile, remoteFile):
        if remoteFile.size == localFile.size:
            return None

        LOGGER.debug('%s: Different size: %d != %d.', remoteFile.path,
                localFile.size, remoteFile.size)

        return self.updateFile

    def checkModified(self, localFile, remoteFile):
        if remoteFile.modified == localFile.modified:
            return None

        fileOperation = self.checkChecksum(localFile, remoteFile)
        if fileOperation is not None:
            return fileOperation

        LOGGER.debug('%s: Different modified time: %s != %s.', remoteFile.path,
                localFile.modified, remoteFile.modified)

        return self.touch

    def insertFolder(self, localFile, remoteFile):
        LOGGER.info('%s: Inserting folder... (Checked %d/%d files)',
                remoteFile.path, self._summary.checkedFiles, self._summary.totalFiles)
        if self.args.dryRun:
            return remoteFile

        return self.transferManager.insertFolder(localFile, remoteFile)

    def insertFile(self, localFile, remoteFile):
        LOGGER.info('%s: Inserting file... (Checked %d/%d files)',
                remoteFile.path, self._summary.checkedFiles, self._summary.totalFiles)
        if self.args.dryRun:
            return remoteFile

        return self.transferManager.insertFile(localFile, remoteFile)

    def updateFile(self, localFile, remoteFile):
        LOGGER.info('%s: Updating file... (Checked %d/%d files)',
                remoteFile.path, self._summary.checkedFiles, self._summary.totalFiles)
        if self.args.dryRun:
            return remoteFile

        return self.transferManager.updateFile(localFile, remoteFile)

    def touch(self, localFile, remoteFile):
        LOGGER.info('%s: Updating modified date... (Checked %d/%d files)',
                remoteFile.path, self._summary.checkedFiles, self._summary.totalFiles)
        if self.args.dryRun:
            return remoteFile

        return self.transferManager.touch(localFile, remoteFile)

    def createLocalFolder(self, localFile):
        return self.localFolderFactory.create(localFile)

    def createRemoteFolder(self, remoteFile):
        if self.args.dryRun and (not remoteFile.exists):
            return folder.empty(remoteFile)

        return self.remoteFolderFactory.create(remoteFile)

    def logResult(self):
        copiedSize = self._summary.copiedSize
        copiedTime = round(self._summary.copiedTime)
        bS = self._summary.bS

        checkedSize = self._summary.checkedSize

        LOGGER.info('Copied %d files (%d%s / %ds = %d%s) Checked %d files (%d%s)',
                    self._summary.copiedFiles,
                    copiedSize.value, copiedSize.unit, copiedTime,
                    bS.value, bS.unit,
                    self._summary.checkedFiles, checkedSize.value, checkedSize.unit)

GDRsync(args).sync()
