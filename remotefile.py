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
            self._parsedMetadata = json.loads(self._delegate.get('description',
                                                                 '{}'))
        except:
            self._parsedMetadata = {}
        if self._parsedMetadata.get('modifiedDate') is None:
            self._parsedMetadata['modifiedDate'] = self._delegate.get('modifiedDate',
                self._delegate.get('createdDate', None))
        if self._parsedMetadata.get('cs') is None:
            self._parsedMetadata['cs'] = self._delegate.get('md5Checksum')
        if self._parsedMetadata.get('fileSize') is None:
            self._parsedMetadata['fileSize'] = int(self._delegate.get('fileSize', 0))
        if self.link or self.folder:
            del self._parsedMetadata['modifiedDate']
        self._parsedMetadataWithoutMd5 = self._parsedMetadata.copy()
        if 'cs' in self._parsedMetadataWithoutMd5.keys():
            del self._parsedMetadataWithoutMd5['cs']

    @property
    def delegate(self):
        return self._delegate

    @property
    def contentSize(self):
        return self.metadata().get('fileSize')

    @property
    def modified(self):
        modifiedDate = self.metadata().get('modifiedDate')
        return date.fromString(modifiedDate)

    @property
    def contentMd5(self):
        return self.metadata(True).get('cs')

    @property
    def exists(self):
        return 'id' in self._delegate

    @property
    def link(self):
        return self.metadata(True).get('type', '') == 'link'

    def metadata(self, withMd5 = False):
        if withMd5:
            return self._parsedMetadata
        return self._parsedMetadataWithoutMd5

    def withDelegate(self, delegate):
        return RemoteFile(self.path, delegate)

    def select(self, tuple):
        return tuple[1]

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
