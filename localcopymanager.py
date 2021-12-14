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

import localdestmanager
import requestexecutor
import transfermanager


class LocalCopyManager(localdestmanager.LocalDestManager):
    def __init__(self, summary):
        self._summary = summary

    def insertFile(self, sourceFile, destinationFile):
        return self._copyFile(sourceFile, destinationFile)

    def _copyFile(self, sourceFile, destinationFile):
        if not sourceFile.exists:
            raise FileNotFoundError(f'File not found: {sourceFile}')

        def request():
            start = time.time()

            bytesTransferred = 0
            with io.open(sourceFile.path, 'rb') as source:
                with io.open(destinationFile.path, 'wb') as dest:
                    while True:
                        buffer = source.read(transfermanager.CHUNKSIZE)
                        if not buffer:
                            break

                        dest.write(buffer)

                        elapsed = self.elapsed(start)
                        bytesTransferred += len(buffer)
                        self.logProgress(destinationFile.path, elapsed,
                                         bytesTransferred, sourceFile.size,
                                         float(bytesTransferred) / sourceFile.size)

            elapsed = self.elapsed(start)
            self.updateSummary(self._summary, sourceFile.size, elapsed)
            self.logEnd(destinationFile.path, elapsed, sourceFile.size, self._summary.copiedFiles)

        requestexecutor.execute(request)

        return self.touch(sourceFile, destinationFile)

    def updateFile(self, sourceFile, destinationFile):
        return self._copyFile(sourceFile, destinationFile)
