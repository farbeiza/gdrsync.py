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

import binaryunit

class Summary(object):
    def __init__(self):
        self._copiedFiles = 0
        self._copiedSize = 0
        self._copiedTime = 0

        self._checkedFiles = 0
        self._checkedSize = 0

        self._totalFiles = 0

    @property
    def copiedFiles(self):
        return self._copiedFiles

    def addCopiedFiles(self, copiedFiles):
        self._copiedFiles += copiedFiles

    @property
    def copiedSize(self):
        return binaryunit.BinaryUnit(self._copiedSize, 'B')

    def addCopiedSize(self, copiedSize):
        self._copiedSize += copiedSize

    @property
    def bS(self):
        return binaryunit.bS(self._copiedSize, self._copiedTime)

    @property
    def copiedTime(self):
        return self._copiedTime

    def addCopiedTime(self, copiedTime):
        self._copiedTime += copiedTime

    @property
    def checkedFiles(self):
        return self._checkedFiles

    def addCheckedFiles(self, checkedFiles):
        self._checkedFiles += checkedFiles

    @property
    def checkedSize(self):
        return binaryunit.BinaryUnit(self._checkedSize, 'B')

    def addCheckedSize(self, checkedSize):
        self._checkedSize += checkedSize

    @property
    def totalFiles(self):
        return self._totalFiles

    def addTotalFiles(self, totalFiles):
        self._totalFiles += totalFiles
