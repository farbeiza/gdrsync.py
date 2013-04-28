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
parser.add_argument('-n', action = 'store_true',
        help = 'perform a trial run with no changes made', dest = 'dryRun')
parser.add_argument('-r', action = 'store_true',
        help = 'recurse into directories', dest = 'recursive')
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
    logging.getLogger('apiclient.discovery').setLevel(logging.WARNING)
    logging.getLogger('oauth2client.util').setLevel(logging.ERROR)

import binaryunit
import driveutils
import folder
import localfolder
import remotefolder
import requestexecutor
import utils
import virtuallocalfolder

import apiclient.http
import mimetypes
import time

CHUNKSIZE = 1 * utils.MIB

PERCENTAGE = 100.0

DEFAULT_MIME_TYPE = 'application/octet-stream'

LOGGER = logging.getLogger(__name__)

class GDRsync(object):
    def __init__(self, args):
        self.args = args

        self.copiedFiles = 0
        self.copiedSize = 0
        self.copiedTime = 0

        self.checkedFiles = 0
        self.checkedSize = 0

        self.totalFiles = 0

    def sync(self):
        LOGGER.info('Starting...')

        virtualLocalFolder = virtuallocalfolder.create(self.args.localPaths)
        remoteFolder = remotefolder.create(self.args.remotePath)
        self._sync(virtualLocalFolder, remoteFolder)

        self.logResult();

        LOGGER.info('End.')

    def _sync(self, localFolder, remoteFolder):
        remoteFolder = self.trash(localFolder, remoteFolder)

        self.totalFiles += len(localFolder.children)

        remoteFolder = self.copy(localFolder, remoteFolder)

        if not self.args.recursive:
            return

        for localFile in localFolder.folders():
            remoteFile = remoteFolder.children[localFile.name]

            self._sync(self.createLocalFolder(localFile),
                    self.createRemoteFolder(remoteFile))

    def trash(self, localFolder, remoteFolder):
        if not self.args.delete:
            return remoteFolder

        remoteFolder = self.trashDuplicate(localFolder, remoteFolder)
        remoteFolder = self.trashExtraneous(localFolder, remoteFolder)
        remoteFolder = self.trashDifferentType(localFolder, remoteFolder)

        return remoteFolder

    def trashDuplicate(self, localFolder, remoteFolder):
        for remoteFile in remoteFolder.duplicate:
            LOGGER.debug('%s: Duplicate file.', remoteFile.path)

            remoteFile = self.trashFile(remoteFile)

        return remoteFolder.withoutDuplicate()

    def trashFile(self, remoteFile):
        LOGGER.info('%s: Trashing file...', remoteFile.path)
        if self.args.dryRun:
            return remoteFile

        def request():
            return (driveutils.DRIVE.files()
                    .trash(fileId = remoteFile.delegate['id'],
                            fields = driveutils.FIELDS)
                    .execute())

        file = requestexecutor.execute(request)

        return remoteFile.withDelegate(file)

    def trashExtraneous(self, localFolder, remoteFolder):
        output = remoteFolder.withoutChildren()
        for remoteFile in remoteFolder.children.values():
            if remoteFile.name in localFolder.children:
                output.addChild(remoteFile)
                continue

            LOGGER.debug('%s: Extraneous file.', remoteFile.path)

            remoteFile = self.trashFile(remoteFile)

        return output

    def trashDifferentType(self, localFolder, remoteFolder):
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

    def copy(self, localFolder, remoteFolder):
        output = (remoteFolder.withoutChildren()
                .addChildren(remoteFolder.children.values()))
        for localFile in localFolder.children.values():
            self.checkedFiles += 1
            self.checkedSize += localFile.size

            remoteFile = remoteFolder.children.get(localFile.name)

            fileOperation = self.fileOperation(localFile, remoteFile)
            if fileOperation is None:
                continue

            if remoteFile is None:
                remoteFile = remoteFolder.createFile(localFile.name,
                        localFile.folder)
            remoteFile = fileOperation(localFile, remoteFile)

            output.addChild(remoteFile)

        return output

    def fileOperation(self, localFile, remoteFile):
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
                self.checkedFiles, self.totalFiles)

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
                remoteFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return remoteFile

        body = remoteFile.delegate.copy()
        body['modifiedDate'] = str(localFile.modified)
        def request():
            return (driveutils.DRIVE.files().insert(body = body,
                    fields = driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return remoteFile.withDelegate(file)

    def insertFile(self, localFile, remoteFile):
        LOGGER.info('%s: Inserting file... (Checked %d/%d files)',
                remoteFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return remoteFile

        def createRequest(body, media):
            return (driveutils.DRIVE.files().insert(body = body,
                    media_body = media, fields = driveutils.FIELDS))

        return self.copyFile(localFile, remoteFile, createRequest)

    def copyFile(self, localFile, remoteFile, createRequest):
        body = remoteFile.delegate.copy()
        body['modifiedDate'] = str(localFile.modified)

        (mimeType, encoding) = mimetypes.guess_type(localFile.delegate)
        if mimeType is None:
            mimeType = DEFAULT_MIME_TYPE

        media = apiclient.http.MediaFileUpload(localFile.delegate,
                mimetype = mimeType, chunksize = CHUNKSIZE, resumable = True)

        def request():
            request = createRequest(body, media)

            start = time.time()
            while True:
                (progress, file) = request.next_chunk()
                if file is not None:
                    self.logProgress(remoteFile.path, start, localFile.size)

                    return file

                self.logProgress(remoteFile.path, start,
                        progress.resumable_progress, progress.total_size,
                        progress.progress(), False)

        file = requestexecutor.execute(request)

        return remoteFile.withDelegate(file)

    def logProgress(self, path, start, bytesUploaded, bytesTotal = None,
            progress = 1.0, end = True):
        if bytesTotal is None:
            bytesTotal = bytesUploaded

        elapsed = time.time() - start

        b = binaryunit.BinaryUnit(bytesUploaded, 'B')
        progressPercentage = round(progress * PERCENTAGE)
        s = round(elapsed)

        bS = binaryunit.BinaryUnit(self.bS(bytesUploaded, elapsed), 'B/s')

        if end:
            self.copiedFiles += 1
            self.copiedSize += bytesTotal
            self.copiedTime += elapsed

            LOGGER.info('%s: %d%% (%d%s / %ds = %d%s) #%d',
                    path, progressPercentage, round(b.value), b.unit, s,
                    round(bS.value), bS.unit, self.copiedFiles)
        else:
            eta = self.eta(elapsed, bytesUploaded, bytesTotal)

            LOGGER.info('%s: %d%% (%d%s / %ds = %d%s) ETA: %ds', path,
                    progressPercentage, round(b.value), b.unit, s,
                    round(bS.value), bS.unit, eta)

    def bS(self, bytesUploaded, elapsed):
        if round(elapsed) == 0:
            return 0

        return bytesUploaded / elapsed

    def eta(self, elapsed, bytesUploaded, bytesTotal):
        if bytesUploaded == 0:
            return 0
        
        bS = bytesUploaded / elapsed
        finish = bytesTotal / bS

        return round(finish - elapsed)

    def updateFile(self, localFile, remoteFile):
        LOGGER.info('%s: Updating file... (Checked %d/%d files)',
                remoteFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return remoteFile

        def createRequest(body, media):
            return (driveutils.DRIVE.files()
                    .update(fileId = remoteFile.delegate['id'], body = body,
                            media_body = media, setModifiedDate = True,
                            fields = driveutils.FIELDS))

        return self.copyFile(localFile, remoteFile, createRequest)

    def touch(self, localFile, remoteFile):
        LOGGER.info('%s: Updating modified date... (Checked %d/%d files)',
                remoteFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return remoteFile

        body = {'modifiedDate': str(localFile.modified)}

        def request():
            return (driveutils.DRIVE.files()
                    .patch(fileId = remoteFile.delegate['id'], body = body,
                            setModifiedDate = True, fields = driveutils.FIELDS)
                    .execute())

        file = requestexecutor.execute(request)

        return remoteFile.withDelegate(file)

    def createLocalFolder(self, localFile):
        return localfolder.create(localFile)

    def createRemoteFolder(self, remoteFile):
        if self.args.dryRun and (not remoteFile.exists):
            return folder.empty(remoteFile)

        return remotefolder.create(remoteFile)

    def logResult(self):
        copiedSize = binaryunit.BinaryUnit(self.copiedSize, 'B')
        copiedTime = round(self.copiedTime)
        bS = binaryunit.BinaryUnit(self.bS(self.copiedSize, self.copiedTime),
                'B/s')

        checkedSize = binaryunit.BinaryUnit(self.checkedSize, 'B')

        LOGGER.info('Copied %d files (%d%s / %ds = %d%s) Checked %d files (%d%s)',
                self.copiedFiles, round(copiedSize.value), copiedSize.unit,
                copiedTime, round(bS.value), bS.unit, self.checkedFiles,
                round(checkedSize.value), checkedSize.unit)

GDRsync(args).sync()
