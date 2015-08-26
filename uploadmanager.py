#!/usr/bin/python

import binaryunit
import driveutils
import requestexecutor
import transfermanager
import utils

import apiclient.http
import logging
import mimetypes
import time

CHUNKSIZE = 1 * utils.MIB

DEFAULT_MIME_TYPE = 'application/octet-stream'

PERCENTAGE = 100.0

LOGGER = logging.getLogger(__name__)

class UploadManager(transfermanager.TransferManager):
    def __init__(self, drive, summary):
        self._drive = drive
        self._summary = summary

    def insertFolder(self, sourceFile, destinationFile):
        body = destinationFile.delegate.copy()
        body['modifiedDate'] = str(sourceFile.modified)
        def request():
            return (self._drive.files().insert(body = body,
                    fields = driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)

    def insertFile(self, sourceFile, destinationFile):
        def createRequest(body, media):
            return (self._drive.files().insert(body = body, media_body = media,
                    fields = driveutils.FIELDS))

        return self._copyFile(sourceFile, destinationFile, createRequest)

    def _copyFile(self, sourceFile, destinationFile, createRequest):
        body = destinationFile.delegate.copy()
        body['modifiedDate'] = str(sourceFile.modified)

        (mimeType, encoding) = mimetypes.guess_type(sourceFile.delegate)
        if mimeType is None:
            mimeType = DEFAULT_MIME_TYPE

        resumable = (sourceFile.size > CHUNKSIZE)
        media = apiclient.http.MediaFileUpload(sourceFile.delegate,
                mimetype = mimeType, chunksize = CHUNKSIZE,
                resumable = resumable)

        def request():
            request = createRequest(body, media)

            start = time.time()
            if not resumable:
                file = request.execute()
                self._logProgress(destinationFile.path, start, sourceFile.size)

                return file

            while True:
                (progress, file) = request.next_chunk()
                if file is not None:
                    self._logProgress(destinationFile.path, start, sourceFile.size)

                    return file

                self._logProgress(destinationFile.path, start,
                        progress.resumable_progress, progress.total_size,
                        progress.progress(), False)

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)

    def _logProgress(self, path, start, bytesUploaded, bytesTotal = None,
            progress = 1.0, end = True):
        if bytesTotal is None:
            bytesTotal = bytesUploaded

        elapsed = time.time() - start

        b = binaryunit.BinaryUnit(bytesUploaded, 'B')
        progressPercentage = round(progress * PERCENTAGE)
        s = round(elapsed)

        bS = binaryunit.bS(bytesUploaded, elapsed)

        if end:
            self._summary.addCopiedFiles(1)
            self._summary.addCopiedSize(bytesTotal)
            self._summary.addCopiedTime(elapsed)

            LOGGER.info('%s: %d%% (%d%s / %ds = %d%s) #%d',
                    path, progressPercentage, round(b.value), b.unit, s,
                    round(bS.value), bS.unit, self._summary.copiedFiles)
        else:
            eta = self._eta(elapsed, bytesUploaded, bytesTotal)

            LOGGER.info('%s: %d%% (%d%s / %ds = %d%s) ETA: %ds', path,
                    progressPercentage, round(b.value), b.unit, s,
                    round(bS.value), bS.unit, eta)

    def _eta(self, elapsed, bytesUploaded, bytesTotal):
        if bytesUploaded == 0:
            return 0

        bS = bytesUploaded / elapsed
        finish = bytesTotal / bS

        return round(finish - elapsed)

    def updateFile(self, sourceFile, destinationFile):
        def createRequest(body, media):
            return (self._drive.files()
                    .update(fileId = destinationFile.delegate['id'], body = body,
                            media_body = media, setModifiedDate = True,
                            fields = driveutils.FIELDS))

        return self._copyFile(sourceFile, destinationFile, createRequest)

    def remove(self, destinationFile):
        def request():
            return (self._drive.files()
                    .trash(fileId = destinationFile.delegate['id'], fields = driveutils.FIELDS)
                    .execute())

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)

    def touch(self, sourceFile, destinationFile):
        body = {'modifiedDate': str(sourceFile.modified)}

        def request():
            request = (self._drive.files()
                    .patch(fileId = destinationFile.delegate['id'], body = body,
                            setModifiedDate = True, fields = driveutils.FIELDS))
            # Ignore Etags
            request.headers['If-Match'] = '*'

            return request.execute()

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)
