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
