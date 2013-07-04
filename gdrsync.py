#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os

parser = argparse.ArgumentParser(description = 'Synchronize between a local'
        ' system and a Google drive repository.')

parser.add_argument('sourcePaths', nargs='+',
        help = ('source paths. A trailing %s means "copy the contents of this'
                ' directory", as opposed to "copy the directory itself"'
                % os.path.sep),
        metavar = 'SOURCE')
parser.add_argument('targetPath', help = 'target path', metavar = 'TARGET')

parser.add_argument('-c', action = 'store_true',
        help = 'skip based on checksum, not mod-time & size', dest = 'checksum')
parser.add_argument('-d', action = 'store_true',
        help = 'delete duplicate and extraneous files from dest dirs',
        dest = 'delete')
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
    logging.getLogger('apiclient.discovery').setLevel(logging.WARNING)
    logging.getLogger('oauth2client.util').setLevel(logging.ERROR)

import binaryunit
import context
import driveutils
import folder
import requestexecutor
import transfer
import utils

import apiclient.http
import errno
import io
import json
import mimetypes
import shutil
import time

CHUNKSIZE = 1 * utils.MIB

PERCENTAGE = 100.0

DEFAULT_MIME_TYPE = 'application/octet-stream'

LOGGER = logging.getLogger(__name__)

class GDRsync(context.Context):
    def __init__(self, args):
        self.args = args

        (self._drive, self._http) = driveutils.drive(self.args.saveCredentials)
        self.batch = None
        self.nbBatch = 0

        self.copiedFiles = 0
        self.copiedSize = 0
        self.copiedTime = 0
        self.checkedFiles = 0
        self.checkedSize = 0
        self.totalFiles = 0

        self.folderFactory = folder.Factory(self.drive, self)

    @property
    def drive(self):
        return self._drive

    @property
    def http(self):
        return self._http

    def sync(self):
        LOGGER.info('Starting...')

        sourceFolder = self.folderFactory.createVirtual(self.args.sourcePaths)
        targetFolder = self.folderFactory.createFromURL(self.args.targetPath)
        self._sync(sourceFolder, targetFolder)
        self._flushBatch()

        self.logResult()

        LOGGER.info('End.')

    def _sync(self, sourceFolder, targetFolder):
        targetFolder = self.trash(sourceFolder, targetFolder)

        self.totalFiles += len(sourceFolder.children)

        targetFolder = self.syncFolder(sourceFolder, targetFolder)

        if not self.args.recursive:
            return

        for sourceFile in sourceFolder.folders():
            targetFile = targetFolder.children[sourceFile.name]

            self._sync(self.createSourceFolder(sourceFile),
                    self.createTargetFolder(targetFile))

    def trash(self, sourceFolder, targetFolder):
        if not self.args.delete:
            return targetFolder

        targetFolder = self.trashDuplicate(sourceFolder, targetFolder)
        targetFolder = self.trashExtraneous(sourceFolder, targetFolder)
        targetFolder = self.trashDifferentType(sourceFolder, targetFolder)

        return targetFolder

    def trashDuplicate(self, sourceFolder, targetFolder):
        for targetFile in targetFolder.duplicate:
            LOGGER.debug('%s: Duplicate file.', targetFile.path)

            self.trashFile(targetFile)

        return targetFolder.withoutDuplicate()

    def trashFile(self, targetFile):
        LOGGER.info('%s: Trashing file...', targetFile.path)
        if self.args.dryRun:
            return targetFile

        transfer.trashFile(self, targetFile)

    def trashExtraneous(self, sourceFolder, targetFolder):
        output = targetFolder.withoutChildren()
        for targetFile in targetFolder.children.values():
            if targetFile.name in sourceFolder.children:
                output.addChild(targetFile)
                continue

            LOGGER.debug('%s: Extraneous file.', targetFile.path)

            self.trashFile(targetFile)

        return output

    def trashDifferentType(self, sourceFolder, targetFolder):
        output = targetFolder.withoutChildren()
        for targetFile in targetFolder.children.values():
            sourceFile = sourceFolder.children[targetFile.name]
            if sourceFile.folder == targetFile.folder:
                output.addChild(targetFile)
                continue

            LOGGER.debug('%s: Different type: %s != %s.', targetFile.path,
                    sourceFile.folder, targetFile.folder)

            self.trashFile(targetFile)

        return output

    def syncFolder(self, sourceFolder, targetFolder):
        output = (targetFolder.withoutChildren()
                .addChildren(targetFolder.children.values()))
        for sourceFile in sourceFolder.children.values():
            self.checkedFiles += 1
            self.checkedSize += sourceFile.size

            try:
                targetFile = self.copy(sourceFile, targetFolder)
                if targetFile is None:
                    continue

                output.addChild(targetFile)
            except OSError as error:
                if error.errno != errno.ENOENT:
                    raise

                LOGGER.warn('%s: No such file or directory.', sourceFile.path)

        return output

    def copy(self, sourceFile, targetFolder):
        targetFile = targetFolder.children.get(sourceFile.name)

        fileOperation = self.fileOperation(sourceFile, targetFile)
        if fileOperation is None:
            return None

        if targetFile is None:
            targetFile = targetFolder.createFile(sourceFile.name,
                    sourceFile.folder)

        return fileOperation(sourceFile, targetFile)

    def fileOperation(self, sourceFile, targetFile):
        if targetFile is None:
            if sourceFile.folder:
                return self.insertFolder

            return self.insertFile

        if (self.args.update and
            not sourceFile.link and
            not sourceFile.folder and
            targetFile.modified > sourceFile.modified):
            LOGGER.debug('%s: Newer destination file: %s < %s.',
                    targetFile.path, sourceFile.modified, targetFile.modified)
        elif self.args.checksum:
            fileOperation = self.checkChecksum(sourceFile, targetFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkSize(sourceFile, targetFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkMetadataModified(sourceFile, targetFile)
            if fileOperation is not None:
                return fileOperation
        else:
            fileOperation = self.checkSize(sourceFile, targetFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkMetadataModified(sourceFile, targetFile)
            if fileOperation is not None:
                return fileOperation

        LOGGER.debug('%s: Up to date. (Checked %d/%d files)', targetFile.path,
                self.checkedFiles, self.totalFiles)

        return None

    def checkChecksum(self, sourceFile, targetFile):
        if targetFile.md5 == sourceFile.md5:
            return None

        LOGGER.debug('%s: Different checksum: %s != %s.', targetFile.path,
                sourceFile.md5, targetFile.md5)

        return self.updateFile

    def checkSize(self, sourceFile, targetFile):
        if targetFile.size == sourceFile.size:
            return None

        LOGGER.debug('%s: Different size: %d != %d.', targetFile.path,
                sourceFile.size, targetFile.size)

        return self.updateFile

    def checkMetadataModified(self, sourceFile, targetFile):
        if (targetFile.metadata() == sourceFile.metadata()):
            return None

        fileOperation = self.checkChecksum(sourceFile, targetFile)
        if fileOperation is not None:
            return fileOperation

        LOGGER.debug('%s: Different metadata: %s != %s.',
                     targetFile.path, sourceFile.metadata(),
                     targetFile.metadata())

        return self.touch

    def insertFolder(self, sourceFile, targetFile):
        LOGGER.info('%s: Inserting folder... (Checked %d/%d files)',
                targetFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return targetFile

        return transfer.insertFolder(self, sourceFile, targetFile)

    def insertFile(self, sourceFile, targetFile):
        LOGGER.info('%s: Inserting file... (Checked %d/%d files)',
                targetFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return targetFile

        return transfer.transferData(self, sourceFile, targetFile)

    def updateFile(self, sourceFile, targetFile):
        LOGGER.info('%s: Updating file... (Checked %d/%d files)',
                targetFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return targetFile

        return transfer.transferData(self, sourceFile, targetFile)

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

    def touch(self, sourceFile, targetFile):
        LOGGER.info('%s: Updating metadata... (Checked %d/%d files)',
                targetFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return targetFile

        return transfer.touchFile(self, sourceFile, targetFile)

    def createSourceFolder(self, sourceFile):
        return self.folderFactory.create(sourceFile)

    def createTargetFolder(self, targetFile):
        if self.args.dryRun and (not targetFile.exists):
            return self.folderFactory.createEmpty(targetFile)

        return self.folderFactory.create(targetFile)

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

    def addToBatch(self, request, callback = None):
        if not self.batch:
            self.batch = apiclient.http.BatchHttpRequest()
        self.batch.add(request, callback)
        self.nbBatch += 1
        if self.nbBatch > 500:
            self._flushBatch()

    def addToBatchAndExecute(self, request):
	# If there is only one request to execute, do not bother setting up a
	# batch.
        if not self.batch:
            return requestexecutor.execute(request)

        results = {}
        def callback(id, result, exception):
            results['id'] = id
            results['result'] = result
            results['exception'] = exception
        self.addToBatch(request, callback)
        self._flushBatch()
        return results.get('result')

    def _flushBatch(self):
        if not self.batch:
            return
        requestexecutor.execute(self.batch.execute)
        self.batch = None
        self.nbBatch = 0

GDRsync(args).sync()
