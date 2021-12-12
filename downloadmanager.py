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

import io
import time

import apiclient.http

import driveutils
import localdestmanager
import requestexecutor
import transfermanager


class DownloadManager(localdestmanager.LocalDestManager):
    def __init__(self, drive, summary):
        self._drive = drive
        self._summary = summary

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
        with io.open(destinationFile.path, 'wb') as dest:
            pass

    def _copyNonEmptyFile(self, sourceFile, destinationFile):
        def createMedia(fileObject):
            request = (self._drive.files()
                       .get_media(fileId=sourceFile.delegate['id'],
                                  fields=driveutils.FIELDS))

            return apiclient.http.MediaIoBaseDownload(fileObject, request,
                                                      chunksize=transfermanager.CHUNKSIZE)

        def request():
            start = time.time()

            with io.open(destinationFile.path, 'wb') as dest:
                media = createMedia(dest)
                while True:
                    (progress, file) = media.next_chunk()

                    elapsed = self.elapsed(start)
                    if file is not None:
                        self.updateSummary(self._summary, sourceFile.size, elapsed)
                        self.logEnd(destinationFile.location, elapsed, sourceFile.size,
                                    self._summary.copiedFiles)

                        return file

                    self.logProgress(destinationFile.location, elapsed,
                                     progress.resumable_progress, progress.total_size,
                                     progress.progress())

        requestexecutor.execute(request)

    def updateFile(self, sourceFile, destinationFile):
        return self._copyFile(sourceFile, destinationFile)
