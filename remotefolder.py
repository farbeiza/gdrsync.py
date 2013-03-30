#!/usr/bin/python

import driveutils
import folder
import remotefile
import requestexecutor

import os

class RemoteFolder(folder.Folder):
    def __init__(self, file, children = {}, duplicate = []):
        super(RemoteFolder, self).__init__(file, children, duplicate)

    def withoutDuplicate(self):
        return RemoteFolder(self._file, self._children)

    def createRemoteFile(self, name, mimeType = None):
        file = {'title': name}
        if mimeType is not None:
            file['mimeType'] = mimeType

        file['parents'] = [{'id': self.file.delegate['id']}]

        return remotefile.fromParent(self.file, file)

CHILDREN_QUERY = '(\'%(parents)s\' in parents) and (not trashed)'

CHILDREN_FIELDS = 'nextPageToken, items(%s)' % driveutils.FIELDS

class Factory(object):
    def create(self, file):
        if not isinstance(file, remotefile.RemoteFile):
            return self.create(remotefile.Factory().create(file))

        query = CHILDREN_QUERY % {'parents': file.delegate['id']}

        def request():
            remoteFolder = RemoteFolder(file)

            list = (driveutils.DRIVE.files()
                    .list(q = query, fields = CHILDREN_FIELDS))
            pageToken = None
            while True:
                if pageToken is not None:
                    list['pageToken'] = pageToken

                files = list.execute()
                for child in files['items']:
                    remoteFolder.addChild(remotefile.fromParent(file, child))

                pageToken = files.get('nextPageToken')
                if not pageToken:
                    break

            return remoteFolder

        return requestexecutor.execute(request)
