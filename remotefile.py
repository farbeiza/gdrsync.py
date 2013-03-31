#!/usr/bin/python

import driveutils
import requestexecutor

import os

def fromParent(parent, delegate):
    return fromParentPath(parent.path, delegate)

def fromParentPath(parentPath, delegate):
    path = os.path.join(parentPath, delegate['title'])

    return RemoteFile(path, delegate)

class RemoteFile(object):
    def __init__(self, path, delegate):
        self._path = path
        self._delegate = delegate

    @property
    def delegate(self):
        return self._delegate

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._delegate['title']

    @property
    def size(self):
        return int(self._delegate['fileSize'])

    @property
    def modified(self):
        return self._delegate['modifiedDate']

    @property
    def md5(self):
        return self._delegate['md5Checksum']

    @property
    def folder(self):
        return self._delegate['mimeType'] == driveutils.MIME_FOLDER

    def withDelegate(self, delegate):
        return RemoteFile(self._path, delegate)

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
        parent, name = os.path.split(path)
        if parent == path:
            return 'root'

        parentId = self.fileId(parent)
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
