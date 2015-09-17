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

import copy
import os.path
import posixpath
import urllib.parse
import urllib.request

REMOTE_SCHEME = 'gdrive'
LOCAL_SCHEME = 'file'

URL_SEPARATOR = '/'

def create(string):
    url = urllib.parse.urlparse(string)
    if url.scheme == REMOTE_SCHEME:
        return RemoteUrl(url)
    if url.scheme == LOCAL_SCHEME:
        return LocalUrl(url)

    return LocalPath(string)

class Location(object):
    @property
    def path(self):
        raise NotImplementedError()

    @property
    def name(self):
        raise NotImplementedError()

    @property
    def parent(self):
        raise NotImplementedError()

    @property
    def remote(self):
        raise NotImplementedError()

    @property
    def contents(self):
        raise NotImplementedError()

    def join(self, path):
        raise NotImplementedError()

class Url(Location):
    def __init__(self, url):
        self._url = url

    @property
    def path(self):
        return urllib.request.url2pathname(self._path)

    @property
    def _path(self):
        path = self._url.path
        if path == '':
            return path

        path = path.rstrip(URL_SEPARATOR)
        if path == '':
            return URL_SEPARATOR

        return path

    @property
    def name(self):
        return posixpath.basename(self._path)

    @property
    def parent(self):
        parentPath = posixpath.dirname(self._path)
        if parentPath == self._path:
            return None

        return self._withPath(parentPath)

    def _withPath(self, newPath):
        return self.create(urllib.parse.ParseResult(self._url.scheme, self._url.netloc, newPath,
                                                    self._url.params, self._url.query,
                                                    self._url.fragment))
    def create(self, url):
        raise NotImplementedError()

    @property
    def contents(self):
        return self._url.path.endswith(URL_SEPARATOR)

    def join(self, path):
        newPath = self._path
        newPath = newPath + URL_SEPARATOR
        newPath = urllib.parse.urljoin(newPath, path)

        return self._withPath(newPath)

    def __str__(self):
        return urllib.parse.urlunparse(self._url)

class RemoteUrl(Url):
    @property
    def remote(self):
        return True

    def create(self, url):
        return RemoteUrl(url)

class LocalUrl(Url):
    @property
    def remote(self):
        return False

    def create(self, url):
        return LocalUrl(url)

class LocalPath(Location):
    def __init__(self, path):
        self._path = path

    @property
    def path(self):
        path = self._path
        if path == '':
            return path

        path = path.rstrip(os.path.sep)
        if path == '':
            return os.path.sep

        return path

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def parent(self):
        parentPath = os.path.dirname(self.path)
        if parentPath == self.path:
            return None

        return LocalPath(parentPath)

    @property
    def remote(self):
        return False

    @property
    def contents(self):
        return self._path.endswith(os.path.sep)

    def join(self, path):
        return LocalPath(os.path.join(self._path, path))

    def __str__(self):
        return str(self._path)
