#!/usr/bin/python

import binaryunit
import driveutils
import requestexecutor
import transfermanager
import utils

import apiclient.http
import io
import logging
import mimetypes
import os
import time

CHUNKSIZE = 1 * utils.MIB

PERCENTAGE = 100.0

LOGGER = logging.getLogger(__name__)

class DownloadManager(transfermanager.TransferManager):
    def __init__(self, drive, summary):
        self._drive = drive
        self._summary = summary

    def insertFolder(self, sourceFile, destinationFile):
        os.mkdir(destinationFile.path)

        return self.touch(sourceFile, destinationFile)

    def insertFile(self, sourceFile, destinationFile):
        return self._copyFile(sourceFile, destinationFile)

    def _copyFile(self, sourceFile, destinationFile):
        if sourceFile.size <= 0:
            self._copyEmptyFile(sourceFile, destinationFile)
        else:
            self._copyNonEmptyFile(sourceFile, destinationFile)

        return self.touch(sourceFile, destinationFile)

    def _copyEmptyFile(self, sourceFile, destinationFile):
        # Empty files raises an error when downloading, so just truncate the file
        with io.open(destinationFile.path, 'wb') as fileObject:
            pass

    def _copyNonEmptyFile(self, sourceFile, destinationFile):
        def createMedia(fileObject):
            request = (self._drive.files()
                       .get_media(fileId = sourceFile.delegate['id'],
                                  fields = driveutils.FIELDS))

            return apiclient.http.MediaIoBaseDownload(fileObject, request, chunksize = CHUNKSIZE)

        def request():
            with io.open(destinationFile.path, 'wb') as fileObject:
                media = createMedia(fileObject)

                start = time.time()
                while True:
                    (progress, file) = media.next_chunk()
                    if file is not None:
                        self._logProgress(destinationFile.path, start, sourceFile.size)

                        return file

                    self._logProgress(destinationFile.path, start,
                                      progress.resumable_progress, progress.total_size,
                                      progress.progress(), False)

        requestexecutor.execute(request)

    def _logProgress(self, path, start, bytesTransferred, bytesTotal = None,
            progress = 1.0, end = True):
        if bytesTotal is None:
            bytesTotal = bytesTransferred

        elapsed = time.time() - start

        b = binaryunit.BinaryUnit(bytesTransferred, 'B')
        progressPercentage = round(progress * PERCENTAGE)
        s = round(elapsed)

        bS = binaryunit.bS(bytesTransferred, elapsed)

        if end:
            self._summary.addCopiedFiles(1)
            self._summary.addCopiedSize(bytesTotal)
            self._summary.addCopiedTime(elapsed)

            LOGGER.info('%s: %d%% (%d%s / %ds = %d%s) #%d',
                    path, progressPercentage, round(b.value), b.unit, s,
                    round(bS.value), bS.unit, self._summary.copiedFiles)
        else:
            eta = self._eta(elapsed, bytesTransferred, bytesTotal)

            LOGGER.info('%s: %d%% (%d%s / %ds = %d%s) ETA: %ds', path,
                    progressPercentage, round(b.value), b.unit, s,
                    round(bS.value), bS.unit, eta)

    def _eta(self, elapsed, bytesTransferred, bytesTotal):
        if bytesTransferred == 0:
            return 0

        bS = bytesTransferred / elapsed
        finish = bytesTotal / bS

        return round(finish - elapsed)

    def updateFile(self, sourceFile, destinationFile):
        return self._copyFile(sourceFile, destinationFile)

    def remove(self, destinationFile):
        if destinationFile.folder:
            shutil.rmtree(destinationFile.path)
        else:
            os.remove(destinationFile.path)

        return destinationFile.copy()

    def touch(self, sourceFile, destinationFile):
        os.utime(destinationFile.path,
                 times = (sourceFile.modified.seconds, sourceFile.modified.seconds))

        return destinationFile.copy()
