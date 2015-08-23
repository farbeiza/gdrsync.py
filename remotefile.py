#!/usr/bin/python

import date
import driveutils
import file
import requestexecutor
import utils

import posixpath

MIME_FOLDER = 'application/vnd.google-apps.folder'

FILE_ID_QUERY = '(title = \'%(title)s\') and (not trashed)'

def fromParent(parent, delegate):
    return fromParentPath(parent.path, delegate)

def fromParentPath(parentPath, delegate):
    path = posixpath.join(parentPath, delegate['title'])

    return RemoteFile(path, delegate)

class RemoteFile(file.File):
    def __init__(self, path, delegate, folder = None):
        parent = path
        name = delegate['title']
        folder = utils.firstNonNone(folder,
                delegate.get('mimeType') == MIME_FOLDER)

        super(RemoteFile, self).__init__(path, name, folder)

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
        return RemoteFile(self.path, delegate)

class Factory(object):
    def __init__(self, drive):
        self.drive = drive

    def create(self, path):
        fileId = self.retrieveFileId(path)
        if fileId is None:
            raise RuntimeError('%s not found' % path)

        def request():
            return (self.drive.files().get(fileId = fileId,
                    fields = driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return RemoteFile(path, file)

    def retrieveFileId(self, path):
        (parent, name) = posixpath.split(path)
        if parent == path:
            return 'root'
        if name == '':
            return self.retrieveFileId(parent)

        parentId = self.retrieveFileId(parent)
        if parentId is None:
            return None

        query = (FILE_ID_QUERY %
                {'title' : driveutils.escapeQueryParameter(name)})
        def request():
            return (self.drive.children().list(folderId = parentId, q = query,
                    maxResults = 1, fields = 'items(id)') .execute())

        children = requestexecutor.execute(request)
        for child in children.get('items'):
            return child['id']

        return None
