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
parser.add_argument('-R', action='store_true', default = False,
        help = 'Download file from Drive', dest = 'download')

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

class GDRsync(object):
    class DownloadDelegate(object):
        def __init__(self, gdrSync):
            self.gdrSync = gdrSync

        def initialSourceFolder(self):
            return self.gdrSync.remoteFolderFactory.create(self.gdrSync.args.sourcePaths[0])

        def initialTargetFolder(self):
            return self.gdrSync.localFolderFactory.create(self.gdrSync.args.targetPath)

        def createSourceFolder(self, sourceFile):
            return self.gdrSync.remoteFolderFactory.create(sourceFile)

        def createTargetFolder(self, targetFile):
            return self.gdrSync.localFolderFactory.create(targetFile)

        def createEmptyTargetFolder(self, targetFile):
            return self.gdrSync.localFolderFactory.createEmpty(targetFile)

        def trashFile(self, targetFile):
            if targetFile.folder:
                shutil.rmtree(targetFile.path)
            else:
                os.unlink(targetFile.path)

        def insertFolder(self, sourceFile, targetFile):
            os.makedirs(targetFile.path)
            return self.touch(sourceFile, targetFile)

        def insertFile(self, sourceFile, targetFile):
            if sourceFile.link:
                os.symlink(sourceFile.metadata()['target'], targetFile.path)
            else:
                self._download(sourceFile, targetFile)
            return self.touch(sourceFile, targetFile)

        def updateFile(self, sourceFile, targetFile):
            os.unlink(targetFile.path)
            return self.insertFile(sourceFile, targetFile)

        def touch(self, sourceFile, targetFile):
            metadata = sourceFile.metadata()
            os.lchown(targetFile.path,
                      metadata.get('uid', -1),
                      metadata.get('gid', -1))
            if sourceFile.link:
                if hasattr(os, 'lchmod'):
                    os.lchmod(targetFile.path, 0777)
            elif metadata.get('mode'):
                os.chmod(targetFile.path, metadata.get('mode'))
            if not sourceFile.link:
                os.utime(targetFile.path, (sourceFile.modified.seconds,
                                           sourceFile.modified.seconds))

            return targetFile

        def _download(self, sourceFile, targetFile):
            def request():
                http_request = apiclient.http.HttpRequest(
                    self.gdrSync.http,
                    None,
                    sourceFile.delegate.get('downloadUrl'),
                    headers = {})
                downloader = apiclient.http.MediaIoBaseDownload(self._openFile(targetFile),
                                                                http_request,
                                                                chunksize=CHUNKSIZE)

                start = time.time()
                while True:
                    (progress, done) = downloader.next_chunk()
                    if file is not None:
                        self.gdrSync.logProgress(targetFile.path, start, sourceFile.size)

                        return done

                    self.gdrSync.logProgress(targetFile.path, start,
                            progress.resumable_progress, progress.total_size,
                            progress.progress(), False)
            requestexecutor.execute(request)

        def _openFile(self, targetFile):
            return io.open(targetFile.path, 'wb')

    class UploadDelegate(object):
        def __init__(self, gdrSync):
            self.gdrSync = gdrSync

        def initialSourceFolder(self):
            return self.gdrSync.virtualLocalFolderFactory.create(self.gdrSync.args.sourcePaths)

        def initialTargetFolder(self):
            return self.gdrSync.remoteFolderFactory.create(self.gdrSync.args.targetPath)

        def createSourceFolder(self, sourceFile):
            return self.gdrSync.localFolderFactory.create(sourceFile)

        def createTargetFolder(self, targetFile):
            return self.gdrSync.remoteFolderFactory.create(targetFile)

        def createEmptyTargetFolder(self, targetFile):
            return self.gdrSync.remoteFolderFactory.createEmpty(targetFile)

        def trashFile(self, targetFile):
            def request():
                return (self.gdrSync.drive.files()
                        .trash(fileId = targetFile.delegate['id'],
                                fields = driveutils.FIELDS)
                        .execute())
            file = requestexecutor.execute(request)
            return targetFile.withDelegate(file)

        def insertFolder(self, sourceFile, targetFile):
            body = targetFile.delegate.copy()
            body['description'] = self._metadata(sourceFile)
            def request():
                return (self.gdrSync.drive.files().insert(body = body,
                        fields = driveutils.FIELDS).execute())

            file = requestexecutor.execute(request)

            return targetFile.withDelegate(file)

        def insertFile(self, sourceFile, targetFile):
            def createRequest(body, media):
                return (self.gdrSync.drive.files().insert(body = body,
                        media_body = media,
                        fields = driveutils.FIELDS))

            return self._copyFile(sourceFile, targetFile, createRequest)

        def updateFile(self, sourceFile, targetFile):
            def createRequest(body, media):
                return (self.gdrSync.drive.files()
                        .update(fileId = targetFile.delegate['id'], body = body,
                                media_body = media, setModifiedDate = True,
                                fields = driveutils.FIELDS))

            return self._copyFile(sourceFile, targetFile, createRequest)

        def touch(self, sourceFile, targetFile):
            body = {'description': self._metadata(sourceFile)}

            def request():
                return (self.gdrSync.drive.files()
                        .patch(fileId = targetFile.delegate['id'], body = body,
                                setModifiedDate = True, fields = driveutils.FIELDS)
                        .execute())

            file = requestexecutor.execute(request)

            return targetFile.withDelegate(file)

        def _metadata(self, sourceFile):
            return json.dumps(sourceFile.metadata(withMd5 = True))

        def _copyFile(self, sourceFile, targetFile, createRequest):
            body = targetFile.delegate.copy()
            body['description'] = self._metadata(sourceFile)

            (mimeType, _) = mimetypes.guess_type(sourceFile.path)
            if mimeType is None:
                mimeType = DEFAULT_MIME_TYPE

            resumable = (sourceFile.size > CHUNKSIZE)
            if sourceFile.link:
                media = None
            else:
              media = apiclient.http.MediaIoBaseUpload(
                      self._openFile(sourceFile),
                      mimetype = mimeType, chunksize = CHUNKSIZE,
                      resumable = resumable)

            def request():
                request = createRequest(body, media)

                start = time.time()
                if not resumable:
                    file = request.execute()
                    self.gdrSync.logProgress(targetFile.path, start, sourceFile.size)

                    return file

                while True:
                    (progress, file) = request.next_chunk()
                    if file is not None:
                        self.gdrSync.logProgress(targetFile.path, start, sourceFile.size)

                        return file

                    self.gdrSync.logProgress(targetFile.path, start,
                            progress.resumable_progress, progress.total_size,
                            progress.progress(), False)

            file = requestexecutor.execute(request)

            return targetFile.withDelegate(file)

        def _openFile(self, sourceFile):
            return io.open(sourceFile.path, 'rb')

    def __init__(self, args):
        self.args = args

        (self.drive, self.http) = driveutils.drive(self.args.saveCredentials)

        self.copiedFiles = 0
        self.copiedSize = 0
        self.copiedTime = 0

        self.checkedFiles = 0
        self.checkedSize = 0

        self.totalFiles = 0

        if self.args.download:
            if len(self.args.sourcePaths) != 1:
                raise RuntimeError('Only one source path if downloading...')
            self.delegate = GDRsync.DownloadDelegate(self)
        else:
            self.delegate = GDRsync.UploadDelegate(self)

        context = None
        self.localFolderFactory = localfolder.Factory(context)
        self.remoteFolderFactory = remotefolder.Factory(self.drive)
        self.virtualLocalFolderFactory = virtuallocalfolder.Factory(context)

    def sync(self):
        LOGGER.info('Starting...')

        sourceFolder = self.delegate.initialSourceFolder()
        targetFolder = self.delegate.initialTargetFolder()
        self._sync(sourceFolder, targetFolder)

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

            targetFile = self.trashFile(targetFile)

        return targetFolder.withoutDuplicate()

    def trashFile(self, targetFile):
        LOGGER.info('%s: Trashing file...', targetFile.path)
        if self.args.dryRun:
            return targetFile

        return self.delegate.trashFile(targetFile)

    def trashExtraneous(self, sourceFolder, targetFolder):
        output = targetFolder.withoutChildren()
        for targetFile in targetFolder.children.values():
            if targetFile.name in sourceFolder.children:
                output.addChild(targetFile)
                continue

            LOGGER.debug('%s: Extraneous file.', targetFile.path)

            targetFile = self.trashFile(targetFile)

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

            targetFile = self.trashFile(targetFile)

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

        return self.delegate.insertFolder(sourceFile, targetFile)

    def insertFile(self, sourceFile, targetFile):
        LOGGER.info('%s: Inserting file... (Checked %d/%d files)',
                targetFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return targetFile

        return self.delegate.insertFile(sourceFile, targetFile)

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

    def updateFile(self, sourceFile, targetFile):
        LOGGER.info('%s: Updating file... (Checked %d/%d files)',
                targetFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return targetFile

        return self.delegate.updateFile(sourceFile, targetFile)

    def touch(self, sourceFile, targetFile):
        LOGGER.info('%s: Updating metadata... (Checked %d/%d files)',
                targetFile.path, self.checkedFiles, self.totalFiles)
        if self.args.dryRun:
            return targetFile

        return self.delegate.touch(sourceFile, targetFile)

    def createSourceFolder(self, sourceFile):
        return self.delegate.createSourceFolder(sourceFile)

    def createTargetFolder(self, targetFile):
        if self.args.dryRun and (not targetFile.exists):
            return self.delegate.createEmptyTargetFolder(targetFile)

        return self.delegate.createTargetFolder(targetFile)

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
