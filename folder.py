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

import utils

class Folder(object):
    def __init__(self, file, children = None, duplicate = None):
        self._file = file
        self._children = utils.firstNonNone(children, {})
        self._duplicate = utils.firstNonNone(duplicate, [])

    def addChild(self, file):
        name = file.location.name
        if name in self._children:
            self._duplicate.append(file)

            return self

        self._children[name] = file

        return self

    def addChildren(self, files):
        for file in files:
            self.addChild(file)

        return self

    @property
    def file(self):
        return self._file

    @property
    def children(self):
        return self._children

    @property
    def duplicate(self):
        return self._duplicate

    def files(self):
        return [child for child in self._children.values() if not child.folder]

    def folders(self):
        return [child for child in self._children.values() if child.folder]

    def withoutChildren(self):
        raise NotImplementedError()

    def withoutDuplicate(self):
        raise NotImplementedError()

    def createFile(self, name, folder = None):
        raise NotImplementedError()

class Factory(object):
    @property
    def remote(self):
        raise NotImplementedError()

    def empty(self, file):
        raise NotImplementedError()

    def create(self, location):
        raise NotImplementedError()

    def virtualFromLocations(self, locations):
        virtualFolder = self.virtual()
        for location in locations:
            if location.contents:
                locationFolder = self.create(location)
                virtualFolder.addChildren(locationFolder.children.values())
            else:
                locationFile = self.fileFactory.create(location)
                virtualFolder.addChild(locationFile)

        return virtualFolder

    def virtual(self):
        raise NotImplementedError()

    @property
    def fileFactory(self):
        raise NotImplementedError()
