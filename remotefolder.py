#!/usr/bin/python

import driveutils
import folder
import remotefile
import requestexecutor
import utils

import os

class RemoteFolder(folder.Folder):
    def __init__(self, file, children = None, duplicate = None):
        super(RemoteFolder, self).__init__(file, children, duplicate)

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

        file['parents'] = [{'id': self.file.delegate['id']}]

        return remotefile.fromParent(self.file, file)

    def createFolder(self, name):
        return self.createFile(name, remotefile.MIME_FOLDER)

CHILDREN_QUERY = '(\'%(parents)s\' in parents) and (not trashed)'

CHILDREN_FIELDS = 'nextPageToken, items(%s)' % driveutils.FIELDS

class Factory(object):
    def create(self, file):
        if not isinstance(file, remotefile.RemoteFile):
            return self.create(remotefile.Factory().create(file))

        query = CHILDREN_QUERY % {'parents': file.delegate['id']}

        def request():
            remoteFolder = RemoteFolder(file)

            pageToken = None
            while True:
                list = (driveutils.DRIVE.files()
                        .list(q = query, fields = CHILDREN_FIELDS,
                                pageToken = pageToken))

                files = list.execute()
                for child in files['items']:
                    remoteFolder.addChild(remotefile.fromParent(file, child))

                pageToken = files.get('nextPageToken')
                if pageToken is None:
                    break

            return remoteFolder

        return requestexecutor.execute(request)
