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
import file
import folder
import remotefile
import requestexecutor
import utils

import os
import posixpath
import urllib.parse

SCHEME = 'gdrive'

CHILDREN_QUERY = '(\'%(parents)s\' in parents) and (not trashed)'
CHILDREN_FIELDS = 'nextPageToken, items(%s)' % driveutils.FIELDS

# https://developers.google.com/drive/v2/reference/files/list#maxResults
LIST_MAX_RESULTS = 1000

class RemoteFolder(folder.Folder):
    def withoutChildren(self):
        return RemoteFolder(self._file)

    def withoutDuplicate(self):
        return RemoteFolder(self._file, self._children)

    def createFile(self, name, folder = None, mimeType = None):
        folder = utils.firstNonNone(folder, False)

        file = {'title': name}
        if mimeType is None:
            if folder:
                file['mimeType'] = remotefile.MIME_FOLDER
        else:
            file['mimeType'] = mimeType

        file['parents'] = [{'id': self.file.delegate.get('id')}]

        return remotefile.fromParent(self.file, file)

    def createFolder(self, name):
        return self.createFile(name, remotefile.MIME_FOLDER)

class Factory(folder.Factory):
    def __init__(self, drive):
        self._drive = drive

    @property
    def remote(self):
        return True

    def empty(self, file):
        return RemoteFolder(file)

    def create(self, file):
        if not isinstance(file, remotefile.RemoteFile):
            if not file.remote:
                raise RuntimeError('Expected a remote location: %s' % file)

            remoteFileFactory = remotefile.Factory(self._drive)

            return self.create(remoteFileFactory.create(file))

        query = CHILDREN_QUERY % {'parents': file.delegate['id']}
        def request():
            remoteFolder = RemoteFolder(file)

            pageToken = None
            while True:
                list = (self._drive.files().list(q = query,
                        fields = CHILDREN_FIELDS, pageToken = pageToken,
                        maxResults = LIST_MAX_RESULTS))

                files = list.execute()
                for child in files['items']:
                    remoteFolder.addChild(remotefile.fromParent(file, child))

                pageToken = files.get('nextPageToken')
                if pageToken is None:
                    break

            return remoteFolder

        return requestexecutor.execute(request)

    def virtual(self):
        return self.empty(file.File(None, None))

    def split(self, path):
        return posixpath.split(path)

    @property
    def fileFactory(self):
        return remotefile.Factory(self._drive)
