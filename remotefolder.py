#!/usr/bin/python

import driveutils
import folder
import remotefile
import requestexecutor

import os

CHILDREN_QUERY = '(\'%(parents)s\' in parents) and (not trashed)'

CHILDREN_FIELDS = "nextPageToken, items(%s)" % driveutils.FIELDS

class Factory:
    def create(self, file):
        if not isinstance(file, remotefile.RemoteFile):
            return self.create(remotefile.Factory().create(file))

        query = CHILDREN_QUERY % {'parents': file.delegate['id']}

        def request():
            remoteFolder = folder.Folder(file)

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