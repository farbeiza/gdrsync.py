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
import os.path
import tempfile
import unittest
import uuid

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


class SyncTestCase(unittest.TestCase):
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

    def test_create_file(self):
        with tempfile.TemporaryDirectory() as expected_path:
            folder_name = 'create_folder'
            file_name = 'create_file'

            expected_folder_path = os.path.join(expected_path, folder_name)
            expected_file_path = os.path.join(expected_folder_path, file_name)

            os.mkdir(expected_folder_path)
            self.file_write_random_line(expected_file_path)

            args = argumentparser.PARSER.parse_args(args=['-r', expected_path + '/', REMOTE_URL])
            sync.Sync(args).sync()

            with tempfile.TemporaryDirectory() as actual_path:
                args = argumentparser.PARSER.parse_args(args=['-r', REMOTE_URL + '/', actual_path])
                sync.Sync(args).sync()

                self.assertFolder(actual_path, expected_path, folder_name)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFile(actual_folder_path, expected_folder_path, file_name)

    def test_update_folder(self):
        with tempfile.TemporaryDirectory() as expected_path:
            folder_name = 'update_folder'
            expected_folder_path = os.path.join(expected_path, folder_name)
            os.mkdir(expected_folder_path)

            file_name_1 = 'file_1'
            expected_file_path_1 = os.path.join(expected_folder_path, file_name_1)
            self.file_write_random_line(expected_file_path_1)

            args = argumentparser.PARSER.parse_args(args=['-r', expected_path + '/', REMOTE_URL])
            sync.Sync(args).sync()

            file_name_2 = 'file_2'
            expected_file_path_2 = os.path.join(expected_folder_path, file_name_2)
            self.file_write_random_line(expected_file_path_2)

            args = argumentparser.PARSER.parse_args(args=['-r', expected_path + '/', REMOTE_URL])
            sync.Sync(args).sync()

            with tempfile.TemporaryDirectory() as actual_path:
                args = argumentparser.PARSER.parse_args(args=['-r', REMOTE_URL + '/', actual_path])
                sync.Sync(args).sync()

                self.assertFolder(actual_path, expected_path, folder_name)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFile(actual_folder_path, expected_folder_path, file_name_1)
                self.assertFile(actual_folder_path, expected_folder_path, file_name_2)

    def test_update_file(self):
        with tempfile.TemporaryDirectory() as expected_path:
            file_name = 'update_file'
            expected_file_path = os.path.join(expected_path, file_name)

            self.file_write_random_line(expected_file_path)
            size1 = os.path.getsize(expected_file_path)

            args = argumentparser.PARSER.parse_args(args=['-r', expected_path + '/', REMOTE_URL])
            sync.Sync(args).sync()

            self.file_write_random_line(expected_file_path)
            size2 = os.path.getsize(expected_file_path)

            self.assertNotEqual(size2, size1)

            args = argumentparser.PARSER.parse_args(args=['-r', expected_path + '/', REMOTE_URL])
            sync.Sync(args).sync()

            with tempfile.TemporaryDirectory() as actual_path:
                args = argumentparser.PARSER.parse_args(args=['-r', REMOTE_URL + '/', actual_path])
                sync.Sync(args).sync()

                self.assertFile(actual_path, expected_path, file_name)

    def test_modification_time(self):
        self.modification_time_test('modification_time', 12345.54321)

    def test_millisecond_modification_time(self):
        self.modification_time_test('millisecond_modification_time', 12345.001)

    def test_negative_modification_time(self):
        self.modification_time_test('negative_modification_time', -12345.54321)

    def modification_time_test(self, file_name, time):
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)
            self.file_write_random_line(expected_file_path)
            os.utime(expected_file_path, times=(time, time))

            args = argumentparser.PARSER.parse_args(args=['-r', expected_path + '/', REMOTE_URL])
            sync.Sync(args).sync()

            with tempfile.TemporaryDirectory() as actual_path:
                args = argumentparser.PARSER.parse_args(args=['-r', REMOTE_URL + '/', actual_path])
                sync.Sync(args).sync()

                self.assertFile(actual_path, expected_path, file_name)

    def test_utf8_name(self):
        with tempfile.TemporaryDirectory() as expected_path:
            folder_name = 'utf8文件内容Folder'
            file_name = 'utf8文件内容'

            expected_folder_path = os.path.join(expected_path, folder_name)
            expected_file_path = os.path.join(expected_folder_path, file_name)

            os.mkdir(expected_folder_path)
            self.file_write_random_line(expected_file_path)

            args = argumentparser.PARSER.parse_args(args=['-r', expected_path + '/', REMOTE_URL])
            sync.Sync(args).sync()

            with tempfile.TemporaryDirectory() as actual_path:
                args = argumentparser.PARSER.parse_args(args=['-r', REMOTE_URL + '/', actual_path])
                sync.Sync(args).sync()

                self.assertFolder(actual_path, expected_path, folder_name)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFile(actual_folder_path, expected_folder_path, file_name)

    def file_write_random_line(self, file, mode='a'):
        with open(file, mode=mode) as f:
            f.write(str(uuid.uuid4()))
            f.write('\n')

    def assertFolder(self, first_base, second_base, name):
        first = os.path.join(first_base, name)
        second = os.path.join(second_base, name)

        if not os.path.exists(first):
            self.assertFalse(os.path.exists(second), f'Folder exists: {second}')
        else:
            self.assertTrue(os.path.isdir(first), msg=f'Not a folder: {first}')

            self.assertTrue(os.path.exists(second), f'Folder does not exist: {second}')
            self.assertTrue(os.path.isdir(second), f'Not a folder: {second}')

    def assertFile(self, first_base, second_base, name):
        first = os.path.join(first_base, name)
        second = os.path.join(second_base, name)

        if not os.path.exists(first):
            self.assertFalse(os.path.exists(second), msg=f'File exists: {second}')
        else:
            self.assertTrue(os.path.isfile(first), msg=f'Not a file: {first}')

            self.assertTrue(os.path.exists(second), msg=f'File does not exist: {second}')
            self.assertTrue(os.path.isfile(second), msg=f'Not a file: {second}')

            self.assertTrue(filecmp.cmp(first, second, shallow=False),
                            msg=f'Different file contents: {first} != {second}')

            self.assertModificationTime(first, second)

    def assertModificationTime(self, first_path, second_path):
        first = os.stat(first_path).st_mtime
        second = os.stat(second_path).st_mtime

        self.assertAlmostEqual(first, second, places=3,
                               msg=f'Modification time: {first_path} != {second_path}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
