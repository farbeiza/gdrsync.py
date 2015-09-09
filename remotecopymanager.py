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

import time

class RemoteCopyManager(remotedestmanager.RemoteDestManager):
    def __init__(self, drive, summary):
        super(RemoteCopyManager, self).__init__(drive)

        self._summary = summary

    def insertFile(self, sourceFile, destinationFile):
        return self._copyFile(sourceFile, destinationFile)

    def _copyFile(self, sourceFile, destinationFile):
        body = sourceFile.delegate.copy()
        body['parents'] = destinationFile.delegate['parents']

        def request():
            start = time.time()

            request = (self._drive.files()
                       .copy(fileId = sourceFile.delegate['id'], body = body,
                             fields = driveutils.FIELDS))

            file = request.execute()

            elapsed = self.elapsed(start)
            self.updateSummary(self._summary, sourceFile.size, elapsed)
            self.logEnd(destinationFile.path, elapsed, sourceFile.size,
                        self._summary.copiedFiles)

            return file

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)

    def updateFile(self, sourceFile, destinationFile):
        destinationFile = self.remove(destinationFile)

        return self._copyFile(sourceFile, destinationFile)
