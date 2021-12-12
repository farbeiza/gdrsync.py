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

import logging
import time

import binaryunit
import utils

CHUNKSIZE = 1 * utils.MIB

PERCENTAGE = 100.0

LOGGER = logging.getLogger(__name__)


class TransferManager(object):
    def insertFolder(self, destinationFile):
        raise NotImplementedError()

    def insertFile(self, sourceFile, destinationFile):
        raise NotImplementedError()

    def updateFile(self, sourceFile, destinationFile):
        raise NotImplementedError()

    def remove(self, destinationFile):
        raise NotImplementedError()

    def touch(self, sourceFile, destinationFile):
        raise NotImplementedError()

    def elapsed(self, start):
        return time.time() - start

    def updateSummary(self, summary, size, elapsed):
        summary.addCopiedFiles(1)
        summary.addCopiedSize(size)
        summary.addCopiedTime(elapsed)

    def logEnd(self, location, elapsed, size, copiedFiles):
        logMessage = self._logMessage(location, elapsed, size, 1)

        LOGGER.info('%s #%d', logMessage, copiedFiles)

    def _logMessage(self, location, elapsed, bytesTransferred, progress):
        b = binaryunit.BinaryUnit(bytesTransferred, 'B')
        progressPercentage = round(progress * PERCENTAGE)
        s = round(elapsed)

        bS = binaryunit.bS(bytesTransferred, elapsed)

        return '%s: %d%% (%d%s / %ds = %d%s)' % (location, progressPercentage,
                                                 round(b.value), b.unit, s,
                                                 round(bS.value), bS.unit)

    def logProgress(self, location, elapsed, bytesTransferred, bytesTotal, progress):
        logMessage = self._logMessage(location, elapsed, bytesTransferred, progress)
        eta = self._eta(elapsed, bytesTransferred, bytesTotal)

        LOGGER.info('%s ETA: %ds', logMessage, eta)

    def _eta(self, elapsed, bytesTransferred, bytesTotal):
        if bytesTransferred == 0:
            return 0

        bS = bytesTransferred / elapsed
        finish = bytesTotal / bS

        return round(finish - elapsed)
