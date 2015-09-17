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

import file
import folder
import localfile

import os

class LocalFolder(folder.Folder):
    def withoutChildren(self):
        return LocalFolder(self._file)

    def withoutDuplicate(self):
        return LocalFolder(self._file, self._children)

    def createFile(self, name, folder = None):
        return localfile.fromParent(self.file, name, folder)

class Factory(folder.Factory):
    @property
    def remote(self):
        return False

    def empty(self, file):
        return LocalFolder(file)

    def create(self, file):
        if not isinstance(file, localfile.LocalFile):
            if file.remote:
                raise RuntimeError('Expected a local location: %s' % file)

            localFileFactory = localfile.Factory()

            return self.create(localFileFactory.create(file))

        localFolder = LocalFolder(file)
        for path in os.listdir(file.delegate.path):
            localFile = localfile.fromParent(file, path)
            localFolder.addChild(localFile)

        return localFolder

    def virtual(self):
        return self.empty(file.File(None, None))

    def split(self, path):
        return os.path.split(path)

    @property
    def fileFactory(self):
        return localfile.Factory()
