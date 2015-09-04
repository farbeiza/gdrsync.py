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
import utils

import date
import hashlib
import os.path

MD5_BUFFER_SIZE = 16 * utils.KIB

def fromParent(parent, path, folder = None):
    return fromParentPath(parent.path, path, folder)

def fromParentPath(parentPath, path, folder = None):
    name = os.path.basename(path)
    path = os.path.join(parentPath, name)

    return LocalFile(path, folder)

class LocalFile(file.File):
    def __init__(self, path, folder = None):
        path = path
        name = os.path.basename(path)
        folder = utils.firstNonNone(folder, os.path.isdir(path))

        super(LocalFile, self).__init__(path, name, folder)

    @property
    def delegate(self):
        return self.path

    @property
    def contentSize(self):
        if not self.exists:
            return 0

        return os.path.getsize(self.path)

    @property
    def modified(self):
        return date.fromSeconds(os.path.getmtime(self.path))

    @property
    def contentMd5(self):
        with open(self.path, mode = 'rb') as file:
            md5 = hashlib.md5()
            while True:
                data = file.read(MD5_BUFFER_SIZE)
                if not data:
                    break

                md5.update(data)

        return md5.hexdigest()

    @property
    def exists(self):
        return os.path.exists(self.path)

    @property
    def link(self):
        return os.path.islink(self.path)

    def copy(self):
        return LocalFile(self.path)

class Factory(object):
    def create(self, path):
        if not os.path.exists(path):
            raise RuntimeError('%s not found' % path)

        return LocalFile(path)
