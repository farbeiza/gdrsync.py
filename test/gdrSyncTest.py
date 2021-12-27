#!/usr/bin/python
#
# Copyright 2021 Fernando Arbeiza <fernando.arbeiza@gmail.com>
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

import filecmp
import logging
import math
import os.path
import tempfile
import unittest

import argumentparser
import driveutils
import exception
import location
import remotefolder
import summary
import sync
import uploadmanager

REMOTE_URL = 'gdrive:///test'

logging.basicConfig(level=logging.INFO)


class GdrSyncTestCase(unittest.TestCase):
    drive = None
    remote_factory = None
    remote_location = None

    @classmethod
    def setUpClass(cls):
        cls.drive = driveutils.drive()
        cls.remote_factory = remotefolder.Factory(cls.drive)
        cls.remote_location = location.create(REMOTE_URL)

    @classmethod
    def tearDownClass(cls):
        cls.drive.close()

    def setUp(self):
        self.remove_remote_folder()
        self.create_remote_folder()

    def tearDown(self):
        self.remove_remote_folder()

    def remove_remote_folder(self):
        upload_manager = uploadmanager.UploadManager(self.drive, summary.Summary())
        try:
            remote_folder = self.remote_factory.create(self.remote_location)
            upload_manager.remove(remote_folder.file)
        except exception.NotFoundException as error:
            pass

    def create_remote_folder(self):
        self.remote_factory.create(self.remote_location, create_path=True)

    def test_utf8_name(self):
        source_url = 'file:resource/utf8_name'

        args = argumentparser.PARSER.parse_args(args=['-r', source_url + '/', REMOTE_URL])
        sync.Sync(args).sync()

        with tempfile.TemporaryDirectory() as actual_path:
            args = argumentparser.PARSER.parse_args(args=['-r', REMOTE_URL + '/', actual_path])
            sync.Sync(args).sync()

            source_location = location.create(source_url)

            folder_name = 'utf8文件内容Folder'
            self.assertFolder(actual_path, source_location.path, folder_name)

            actual_file_base = os.path.join(actual_path, folder_name)
            expected_file_base = os.path.join(source_location.path, folder_name)
            self.assertFile(actual_file_base, expected_file_base, 'utf8文件内容')

    def assertFolder(self, first_base, second_base, name):
        first = os.path.join(first_base, name)
        second = os.path.join(second_base, name)

        if not os.path.exists(first):
            if os.path.exists(second):
                raise AssertionError(f'Folder exists: {second}')
        else:
            if not os.path.isdir(first):
                raise AssertionError(f'Not a folder: {first}')

            if not os.path.exists(second):
                raise AssertionError(f'Folder does not exist: {second}')
            if not os.path.isdir(second):
                raise AssertionError(f'Not a folder: {second}')

    def assertFile(self, first_base, second_base, name):
        first = os.path.join(first_base, name)
        second = os.path.join(second_base, name)

        if not os.path.exists(first):
            if os.path.exists(second):
                raise AssertionError(f'File exists: {second}')
        else:
            if not os.path.isfile(first):
                raise AssertionError(f'Not a file: {first}')

            if not os.path.exists(second):
                raise AssertionError(f'File does not exist: {second}')
            if not os.path.isfile(second):
                raise AssertionError(f'Not a file: {second}')

            if not filecmp.cmp(first, second, shallow=False):
                raise AssertionError(f'Different file contents: {first} != {second}')

            self.assertModificationTime(first, second)

    def assertModificationTime(self, first_path, second_path):
        first = os.stat(first_path).st_mtime
        second = os.stat(second_path).st_mtime

        if math.fabs(first - second) > 1e-3:
            raise AssertionError(f'Different modification time: {first} != {second} ({first_path} != {second_path})')


if __name__ == '__main__':
    unittest.main(verbosity=2)