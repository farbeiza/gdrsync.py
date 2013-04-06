#!/usr/bin/python

import driveutils
import file
import requestexecutor
import utils

import os

MIME_FOLDER = 'application/vnd.google-apps.folder'

def fromParent(parent, delegate):
    return fromParentPath(parent.path, delegate)

def fromParentPath(parentPath, delegate):
    path = os.path.join(parentPath, delegate['title'])

    return RemoteFile(path, delegate)

class RemoteFile(file.File):
    def __init__(self, path, delegate, folder = None):
        parent = unicode(path)
        name = delegate['title']
        folder = utils.firstNonNone(folder,
                delegate.get('mimeType') == MIME_FOLDER)

        super(RemoteFile, self).__init__(path, name, folder)

        self._delegate = delegate

    @property
    def delegate(self):
        return self._delegate

    @property
    def size(self):
        return int(self._delegate['fileSize'])

    @property
    def modified(self):
        return driveutils.parseTime(self._delegate['modifiedDate'])

    @property
    def md5(self):
        return self._delegate['md5Checksum']

    @property
    def exists(self):
        return 'id' in self._delegate

    def withDelegate(self, delegate):
        return RemoteFile(self.path, delegate)

FILE_ID_QUERY = '(title = \'%(title)s\') and (not trashed)'

class Factory(object):
    def create(self, path):
        fileId = self.fileId(path)
        if fileId is None:
            raise RuntimeError('%s not found' % path)

        def request():
            return (driveutils.DRIVE.files()
                    .get(fileId = fileId, fields = driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return RemoteFile(path, file)

    def fileId(self, path):
        (parent, name) = os.path.split(path)
        if parent == path:
            return 'root'

        parentId = self.fileId(parent)
        if parentId is None:
            return None

        query = FILE_ID_QUERY % {'title' : driveutils.escapeQueryParameter(name)}

        def request():
            return (driveutils.DRIVE.children()
                    .list(folderId = parentId, q = query, maxResults = 1,
                            fields = 'items(id)')
                    .execute())

        children = requestexecutor.execute(request)
        for child in children.get('items'):
            return child['id']

        return None
