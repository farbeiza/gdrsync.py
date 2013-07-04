#!/usr/bin/python

import date
import driveutils
import file
import json
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
        name = delegate['title']
        folder = utils.firstNonNone(folder,
                delegate.get('mimeType') == MIME_FOLDER)

        super(RemoteFile, self).__init__(path, name, folder)

        self._delegate = delegate
        try:
            self._parsedMetada = json.loads(self._delegate.get('description',
                                                               '{}'))
        except:
            self._parsedMetada = {}
        self._parsedMetadaWithoutMd5 = self._parsedMetada.copy()
        if 'cs' in self._parsedMetadaWithoutMd5.keys():
          del self._parsedMetadaWithoutMd5['cs']

    @property
    def delegate(self):
        return self._delegate

    @property
    def contentSize(self):
        return self.metadata().get('fileSize', -1)

    @property
    def modified(self):
        modifiedDate = self.metadata().get('modifiedDate',
                                           '1970-1-1T00:00:00.0Z')
        return date.fromString(modifiedDate)

    @property
    def contentMd5(self):
        return self.metadata(True).get('cs', '')

    @property
    def exists(self):
        return 'id' in self._delegate

    @property
    def link(self):
        return self.metadata().get('type', '') == 'link'

    def metadata(self, withMd5 = False):
        if withMd5:
            return self._parsedMetada
        return self._parsedMetadaWithoutMd5

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
