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

import driveutils
import requestexecutor
import transfermanager

class RemoteDestManager(transfermanager.TransferManager):
    def __init__(self, drive):
        self._drive = drive

    def insertFolder(self, sourceFile, destinationFile):
        body = destinationFile.delegate.copy()
        body['modifiedTime'] = str(sourceFile.modified)
        def request():
            return (self._drive.files().create(body = body,
                    fields = driveutils.FIELDS).execute())

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)

    def remove(self, destinationFile):
        def request():
            body = { 'trashed': True }
            return (self._drive.files()
                    .update(fileId = destinationFile.delegate['id'], body = body,
                            fields = driveutils.FIELDS)
                    .execute())

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)

    def touch(self, sourceFile, destinationFile):
        body = {'modifiedTime': str(sourceFile.modified)}

        def request():
            request = (self._drive.files()
                       .update(fileId = destinationFile.delegate['id'], body = body,
                               fields = driveutils.FIELDS))
            # Ignore Etags
            request.headers['If-Match'] = '*'

            return request.execute()

        file = requestexecutor.execute(request)

        return destinationFile.withDelegate(file)
