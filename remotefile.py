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

import date
import driveutils
import file
import requestexecutor
import utils

import posixpath

MIME_FOLDER = 'application/vnd.google-apps.folder'

FILE_ID_QUERY = '(title = \'%(title)s\') and (not trashed)'

def fromParent(parent, delegate):
    return fromParentLocation(parent.location, delegate)

def fromParentLocation(parentLocation, delegate):
    location = parentLocation.join(delegate['title'])

    return RemoteFile(location, delegate)

class RemoteFile(file.File):
    def __init__(self, location, delegate, folder = None):
        folder = utils.firstNonNone(folder,
                delegate.get('mimeType') == MIME_FOLDER)

        super(RemoteFile, self).__init__(location, folder)

        self._delegate = delegate

    @property
    def delegate(self):
        return self._delegate

    @property
    def contentSize(self):
        return int(self._delegate['fileSize'])

    @property
    def modified(self):
        modifiedDate = self._delegate.get('modifiedDate',
                self._delegate['createdDate'])

        return date.fromString(modifiedDate)

    @property
    def contentMd5(self):
        return self._delegate['md5Checksum']

    @property
    def exists(self):
        return 'id' in self._delegate

    def withDelegate(self, delegate):
        return RemoteFile(self.location, delegate)

class Factory(object):
    def __init__(self, drive):
        self.drive = drive

    def create(self, location):
        if not location.remote:
            raise RuntimeError('Expected a remote location: %s' % location)

        fileId = self.retrieveFileId(location)
        if fileId is None:
            raise RuntimeError('%s not found' % location)

        def request():
            return (self.drive.files().get(fileId = fileId,
                    fields = driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return RemoteFile(location, file)

    def retrieveFileId(self, location):
        parent = location.parent
        if parent is None:
            return 'root'

        parentId = self.retrieveFileId(parent)
        if parentId is None:
            return None

        query = (FILE_ID_QUERY %
                {'title' : driveutils.escapeQueryParameter(location.name)})
        def request():
            return (self.drive.children().list(folderId = parentId, q = query,
                    maxResults = 1, fields = 'items(id)') .execute())

        children = requestexecutor.execute(request)
        for child in children.get('items'):
            return child['id']

        return None
