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

import hashlib

import utils


class File(object):
    def __init__(self, location, folder=None):
        self._location = location
        self._folder = utils.firstNonNone(folder, False)

    @property
    def location(self):
        return self._location

    @property
    def folder(self):
        return self._folder

    @property
    def size(self):
        if self.folder:
            return 0

        return self.contentSize

    @property
    def contentSize(self):
        raise NotImplementedError()

    @property
    def md5(self):
        if self.folder:
            md5 = hashlib.md5()
            md5.update(self.location.name.encode('utf-8'))

            return md5.hexdigest()

        return self.contentMd5

    @property
    def contentMd5(self):
        raise NotImplementedError()

    @property
    def exists(self):
        return False

    @property
    def link(self):
        return False

    def __str__(self):
        return str(self.location)
