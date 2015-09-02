#!/usr/bin/python

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

    def isRemote(self):
        return True

    def handlesUrl(self, url):
        return self._pathFromUrl(url) is not None

    def _pathFromUrl(self, urlString):
        url = urllib.parse.urlparse(urlString)
        if url.scheme != SCHEME:
            return None

        return url.path

    def empty(self, file):
        return RemoteFolder(file)

    def pathFromUrl(self, url):
        path = self._pathFromUrl(url)
        if path is None:
            raise RuntimeError('Invalid URL: URL is not a %s one: %s' % (SCHEME, urlString))

        return path

    def create(self, file):
        if not isinstance(file, remotefile.RemoteFile):
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
