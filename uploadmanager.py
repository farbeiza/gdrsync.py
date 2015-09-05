#!/usr/bin/python
#
# Copyright 2015 Fernando Arbeiza <fernando.arbeiza@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import driveutils
import requestexecutor
import transfermanager

import apiclient.http
import mimetypes
import time

DEFAULT_MIME_TYPE = 'application/octet-stream'

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

        resumable = (sourceFile.size > transfermanager.CHUNKSIZE)
        media = apiclient.http.MediaFileUpload(sourceFile.delegate,
                mimetype = mimeType, chunksize = transfermanager.CHUNKSIZE,
                resumable = resumable)

        def request():
            request = createRequest(body, media)

            start = time.time()
            if not resumable:
                file = request.execute()
                elapsed = self.elapsed(start)
                self.updateSummary(self._summary, sourceFile.size, elapsed)
                self.logEnd(destinationFile.path, elapsed, sourceFile.size,
                            self._summary.copiedFiles)

                return file

            while True:
                (progress, file) = request.next_chunk()
                elapsed = self.elapsed(start)
                if file is not None:
                    self.updateSummary(self._summary, sourceFile.size, elapsed)
                    self.logEnd(destinationFile.path, elapsed, sourceFile.size,
                                self._summary.copiedFiles)

                    return file

                self.logProgress(destinationFile.path, elapsed,
                                 progress.resumable_progress, progress.total_size,
                                 progress.progress())

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)

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
