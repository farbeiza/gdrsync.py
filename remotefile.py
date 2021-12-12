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

MIME_FOLDER = 'application/vnd.google-apps.folder'

FILE_ID_QUERY = '(\'%(parentId)s\' in parents) and (name = \'%(name)s\') and (not trashed)'


def fromParent(parent, delegate):
    return fromParentLocation(parent.location, delegate)


def fromParentLocation(parentLocation, delegate):
    location = parentLocation.join(delegate['name'])

    return RemoteFile(location, delegate)


class RemoteFile(file.File):
    def __init__(self, location, delegate, folder=None):
        folder = utils.firstNonNone(folder,
                                    delegate.get('mimeType') == MIME_FOLDER)

        super(RemoteFile, self).__init__(location, folder)

        self._delegate = delegate

    @property
    def delegate(self):
        return self._delegate

    @property
    def contentSize(self):
        return int(self._delegate['size'])

    @property
    def modified(self):
        modifiedTime = self._delegate.get('modifiedTime',
                                          self._delegate['createdTime'])

        return date.fromString(modifiedTime)

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
            return (self.drive.files().get(fileId=fileId,
                                           fields=driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return RemoteFile(location, file)

    def retrieveFileId(self, location):
        parent = location.parent
        if parent is None:
            return self.retrieveRootId()

        parentId = self.retrieveFileId(parent)
        if parentId is None:
            return None

        query = FILE_ID_QUERY % {
            'parentId': driveutils.escapeQueryParameter(parentId),
            'name': driveutils.escapeQueryParameter(location.name)
        }

        def request():
            return (self.drive.files().list(q=query,
                                            pageSize=1, fields='files(id)').execute())

        children = requestexecutor.execute(request)
        for child in children.get('files'):
            return child['id']

        return None

    def retrieveRootId(self):
        root = (self.drive.files().get(fileId='root', fields='id')
                .execute())

        return root['id']
