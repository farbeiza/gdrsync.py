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
import remotedestmanager
import transfermanager

import apiclient.http
import mimetypes
import time
import logging

DEFAULT_MIME_TYPE = 'application/octet-stream'

LOGGER = logging.getLogger(__name__)

class UploadManager(remotedestmanager.RemoteDestManager):
    def __init__(self, drive, summary):
        super(UploadManager, self).__init__(drive)

        self._summary = summary

    def insertFile(self, sourceFile, destinationFile):
        def createRequest(body, media):
            return (self._drive.files().insert(body = body, media_body = media,
                    fields = driveutils.FIELDS))

        return self._copyFile(sourceFile, destinationFile, createRequest)

    def _copyFile(self, sourceFile, destinationFile, createRequest):
        body = destinationFile.delegate.copy()
        body['modifiedDate'] = str(sourceFile.modified)

        (mimeType, encoding) = mimetypes.guess_type(sourceFile.location.path)
        if mimeType is None:
            mimeType = DEFAULT_MIME_TYPE

        resumable = (sourceFile.size > transfermanager.CHUNKSIZE)
        media = apiclient.http.MediaFileUpload(sourceFile.location.path,
                mimetype = mimeType, chunksize = transfermanager.CHUNKSIZE,
                resumable = resumable)

        def request():
            start = time.time()

            request = createRequest(body, media)
            if not resumable:
                file = request.execute()

                elapsed = self.elapsed(start)
                self.updateSummary(self._summary, sourceFile.size, elapsed)
                self.logEnd(destinationFile.location, elapsed, sourceFile.size,
                            self._summary.copiedFiles)

                return file

            while True:
                (progress, file) = request.next_chunk()
                elapsed = self.elapsed(start)
                if file is not None:
                    self.updateSummary(self._summary, sourceFile.size, elapsed)
                    self.logEnd(destinationFile.location, elapsed, sourceFile.size,
                                self._summary.copiedFiles)

                    return file

                self.logProgress(destinationFile.location, elapsed,
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
