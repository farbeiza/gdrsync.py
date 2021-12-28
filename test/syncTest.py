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
import shutil
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

    def test_should_create_folder(self):
        folder_name = 'create_folder'
        file_name = 'create_file'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_folder_path = os.path.join(expected_path, folder_name)
            expected_file_path = os.path.join(expected_folder_path, file_name)

            os.mkdir(expected_folder_path)
            self.file_write_random_line(expected_file_path)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFolderMatches(actual_path, expected_path, name=folder_name)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFileMatches(actual_folder_path, expected_folder_path, name=file_name)

    def test_should_create_file(self):
        file_name = 'create_file'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)
            self.file_write_random_line(expected_file_path)

            self.sync_file_from_local(expected_file_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_file_from_remote(file_name, actual_path)

                self.assertFileMatches(actual_path, expected_path, name=file_name)

    def test_should_update_folder(self):
        folder_name = 'update_folder'
        file_name_1 = 'file_1'
        file_name_2 = 'file_2'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_folder_path = os.path.join(expected_path, folder_name)
            os.mkdir(expected_folder_path)

            expected_file_path_1 = os.path.join(expected_folder_path, file_name_1)
            self.file_write_random_line(expected_file_path_1)

            self.sync_from_local(expected_path)

            expected_file_path_2 = os.path.join(expected_folder_path, file_name_2)
            self.file_write_random_line(expected_file_path_2)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFolderMatches(actual_path, expected_path, name=folder_name)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFileMatches(actual_folder_path, expected_folder_path, name=file_name_1)
                self.assertFileMatches(actual_folder_path, expected_folder_path, name=file_name_2)

    def test_should_update_file(self):
        file_name = 'update_file'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)

            self.file_write_random_line(expected_file_path)
            stat1 = os.stat(expected_file_path)

            self.sync_file_from_local(expected_file_path)

            self.file_write_random_line(expected_file_path)
            stat2 = os.stat(expected_file_path)

            self.assertNotEqual(stat2.st_size, stat1.st_size)
            self.assertNotEqual(stat2.st_mtime, stat1.st_mtime)

            self.sync_file_from_local(expected_file_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_file_from_remote(file_name, actual_path)

                self.assertFileMatches(actual_path, expected_path, name=file_name)

    def test_should_not_update_file_when_same_size_and_same_modification_time(self):
        file_name = 'update_file'
        time = 12345.54321
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)

            self.file_write_random_line(expected_file_path, mode='w')
            os.utime(expected_file_path, times=(time, time))
            stat1 = os.stat(expected_file_path)

            self.sync_from_local(expected_path)

            self.file_write_random_line(expected_file_path, mode='w')
            os.utime(expected_file_path, times=(time, time))
            stat2 = os.stat(expected_file_path)

            self.assertEqual(stat2.st_size, stat1.st_size)
            self.assertEqual(stat2.st_mtime, stat1.st_mtime)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                actual_file_path = os.path.join(actual_path, file_name)
                self.assertFalse(filecmp.cmp(actual_file_path, expected_file_path, shallow=False),
                                 msg=f'Same file contents: {actual_file_path} != {expected_file_path}')

    def test_should_update_file_when_same_size_and_same_modification_time_and_use_checksum(self):
        file_name = 'update_file'
        time = 12345.54321
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)

            self.file_write_random_line(expected_file_path, mode='w')
            os.utime(expected_file_path, times=(time, time))
            stat1 = os.stat(expected_file_path)

            self.sync_from_local(expected_path, additional_args=['-c'])

            self.file_write_random_line(expected_file_path, mode='w')
            os.utime(expected_file_path, times=(time, time))
            stat2 = os.stat(expected_file_path)

            self.assertEqual(stat2.st_size, stat1.st_size)
            self.assertEqual(stat2.st_mtime, stat1.st_mtime)

            self.sync_from_local(expected_path, additional_args=['-c'])

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFileMatches(actual_path, expected_path, name=file_name)

    def test_should_update_modification_time(self):
        self.modification_time_test('modification_time', 12345.54321)

    def test_should_update_modification_time_when_millisecond_modification_time(self):
        self.modification_time_test('millisecond_modification_time', 12345.001)

    def test_should_update_modification_time_when_negative_modification_time(self):
        self.modification_time_test('negative_modification_time', -12345.54321)

    def modification_time_test(self, file_name, time):
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)
            self.file_write_random_line(expected_file_path)

            self.sync_from_local(expected_path)

            os.utime(expected_file_path, times=(time, time))

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFileMatches(actual_path, expected_path, name=file_name)

    def test_should_update_file_when_special_char_name(self):
        self.update_test('specialCharFolder*?', 'specialChar*?')

    def test_should_update_file_when_utf8_name(self):
        self.update_test('utf8文件内容Folder', 'utf8文件内容')

    def update_test(self, folder_name, file_name):
        with tempfile.TemporaryDirectory() as expected_path:
            expected_folder_path = os.path.join(expected_path, folder_name)
            expected_file_path = os.path.join(expected_folder_path, file_name)

            os.mkdir(expected_folder_path)

            self.file_write_random_line(expected_file_path)
            stat1 = os.stat(expected_file_path)

            self.sync_from_local(expected_path)

            self.file_write_random_line(expected_file_path)
            stat2 = os.stat(expected_file_path)

            self.assertNotEqual(stat2.st_size, stat1.st_size)
            self.assertNotEqual(stat2.st_mtime, stat1.st_mtime)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFolderMatches(actual_path, expected_path, name=folder_name)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFileMatches(actual_folder_path, expected_folder_path, name=file_name)

    def test_should_keep_extraneous_folder(self):
        folder_name = 'extraneous_folder'
        file_name = 'file'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_folder_path = os.path.join(expected_path, folder_name)
            os.mkdir(expected_folder_path)

            expected_file_path = os.path.join(expected_folder_path, file_name)
            self.file_write_random_line(expected_file_path)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFolderMatches(actual_path, expected_path, name=folder_name)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFileMatches(actual_folder_path, expected_folder_path, name=file_name)

                shutil.rmtree(expected_folder_path)
                shutil.rmtree(actual_folder_path)

                self.sync_from_local(expected_path)

                self.sync_from_remote(actual_path)

                self.assertFolderNotFound(expected_folder_path)
                self.assertFileNotFound(expected_file_path)

                actual_file_path = os.path.join(actual_folder_path, file_name)
                self.assertFolder(actual_folder_path)
                self.assertFile(actual_file_path)

    def test_should_delete_extraneous_folder_when_option(self):
        folder_name = 'extraneous_folder'
        file_name = 'file'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_folder_path = os.path.join(expected_path, folder_name)
            os.mkdir(expected_folder_path)

            expected_file_path = os.path.join(expected_folder_path, file_name)
            self.file_write_random_line(expected_file_path)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFolderMatches(actual_path, expected_path, name=folder_name)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFileMatches(actual_folder_path, expected_folder_path, name=file_name)

                shutil.rmtree(expected_folder_path)

                self.sync_from_local(expected_path, additional_args=['--delete'])

                self.sync_from_remote(actual_path, additional_args=['--delete'])

                self.assertFolderNotFoundMatches(actual_path, expected_path, folder_name)
                self.assertFileNotFoundMatches(actual_folder_path, expected_folder_path, file_name)

    def test_should_keep_extraneous_file_when_option(self):
        file_name = 'extraneous_file'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)
            self.file_write_random_line(expected_file_path)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFileMatches(actual_path, expected_path, name=file_name)

                os.remove(expected_file_path)

                self.sync_from_local(expected_path)

                self.sync_from_remote(actual_path)

                self.assertFileNotFound(expected_file_path)

                actual_file_path = os.path.join(actual_path, file_name)
                self.assertFile(actual_file_path)

    def test_should_delete_extraneous_file_when_option(self):
        file_name = 'extraneous_file'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)
            self.file_write_random_line(expected_file_path)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFileMatches(actual_path, expected_path, name=file_name)

                os.remove(expected_file_path)

                self.sync_from_local(expected_path, additional_args=['--delete'])

                self.sync_from_remote(actual_path, additional_args=['--delete'])

                self.assertFileNotFoundMatches(actual_path, expected_path, file_name)

    def test_should_not_create_symbolic_link(self):
        file_name = 'file'
        link_name = 'link'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)
            self.file_write_random_line(expected_file_path)

            expected_link_path = os.path.join(expected_path, link_name)
            os.symlink(expected_file_path, expected_link_path)

            self.sync_from_local(expected_path)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFileMatches(actual_path, expected_path, name=file_name)

                actual_link_path = os.path.join(actual_path, link_name)
                self.assertFile(expected_link_path)
                self.assertFileNotFound(actual_link_path)

    def test_should_create_symbolic_link_to_folder_when_option(self):
        folder_name = 'folder'
        file_name = 'file'
        link_name = 'link'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_folder_path = os.path.join(expected_path, folder_name)
            os.mkdir(expected_folder_path)

            expected_file_path = os.path.join(expected_folder_path, file_name)
            self.file_write_random_line(expected_file_path)

            expected_link_path = os.path.join(expected_path, link_name)
            os.symlink(expected_folder_path, expected_link_path)

            self.sync_from_local(expected_path, additional_args=['-L'])

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                actual_folder_path = os.path.join(actual_path, folder_name)
                self.assertFolderMatches(actual_path, expected_path, name=folder_name)
                self.assertFileMatches(actual_folder_path, expected_folder_path, name=file_name)
                self.assertFolderMatches(actual_path, expected_path, name=link_name)

                actual_link_path = os.path.join(expected_path, link_name)
                self.assertFolderMatches(actual_link_path, expected_folder_path)

                actual_file_path = os.path.join(actual_path, link_name, file_name)
                self.assertFileMatches(actual_file_path, expected_file_path)

    def test_should_create_symbolic_link_to_file_when_option(self):
        file_name = 'file'
        link_name = 'link'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_file_path = os.path.join(expected_path, file_name)
            self.file_write_random_line(expected_file_path)

            expected_link_path = os.path.join(expected_path, link_name)
            os.symlink(expected_file_path, expected_link_path)

            self.sync_from_local(expected_path, additional_args=['-L'])

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFileMatches(actual_path, expected_path, name=file_name)
                self.assertFileMatches(actual_path, expected_path, name=link_name)

                actual_link_path = os.path.join(expected_path, link_name)
                self.assertFileMatches(actual_link_path, expected_file_path)

    def file_write_random_line(self, file, mode='a'):
        with open(file, mode=mode) as f:
            f.write(str(uuid.uuid4()))
            f.write('\n')

    def sync_from_local(self, local_path, additional_args=None):
        if additional_args is None:
            additional_args = []

        self.sync('-r', *additional_args, local_path + os.sep, REMOTE_URL)

    def sync_from_remote(self, local_path, additional_args=None):
        if additional_args is None:
            additional_args = []

        self.sync('-r', *additional_args, REMOTE_URL + location.URL_SEPARATOR, local_path)

    def sync_file_from_local(self, file_path):
        self.sync(file_path, REMOTE_URL)

    def sync_file_from_remote(self, file_name, local_path):
        self.sync(REMOTE_URL + location.URL_SEPARATOR + file_name, local_path)

    def sync(self, *arg_list):
        args = argumentparser.PARSER.parse_args(args=arg_list)

        sync_instance = sync.Sync(args)
        sync_instance.sync()
        sync_instance.close()

    def assertFolder(self, path):
        self.assertTrue(os.path.exists(path), msg=f'Folder does not exist: {path}')
        self.assertTrue(os.path.isdir(path), msg=f'Not a folder: {path}')

    def assertFile(self, path):
        self.assertTrue(os.path.exists(path), msg=f'File does not exist: {path}')
        self.assertTrue(os.path.isfile(path), msg=f'Not a file: {path}')

    def assertFolderMatches(self, first, second, name=None):
        if name is not None:
            first = os.path.join(first, name)
            second = os.path.join(second, name)

        self.assertFolder(first)
        self.assertFolder(second)

    def assertFileMatches(self, first, second, name=None):
        if name is not None:
            first = os.path.join(first, name)
            second = os.path.join(second, name)

        self.assertFile(first)
        self.assertFile(second)

        self.assertTrue(filecmp.cmp(first, second, shallow=False),
                        msg=f'Different file contents: {first} != {second}')

        self.assertModificationTime(first, second)

    def assertFolderNotFound(self, path):
        self.assertFalse(os.path.exists(path), msg=f'Folder exists: {path}')

    def assertFileNotFound(self, path):
        self.assertFalse(os.path.exists(path), msg=f'File exists: {path}')

    def assertFolderNotFoundMatches(self, first_base, second_base, name):
        first = os.path.join(first_base, name)
        second = os.path.join(second_base, name)

        self.assertFolderNotFound(first)
        self.assertFolderNotFound(second)

    def assertFileNotFoundMatches(self, first_base, second_base, name):
        first = os.path.join(first_base, name)
        second = os.path.join(second_base, name)

        self.assertFileNotFound(first)
        self.assertFileNotFound(second)

    def assertModificationTime(self, first_path, second_path):
        first = os.stat(first_path).st_mtime
        second = os.stat(second_path).st_mtime

        self.assertAlmostEqual(first, second, places=3,
                               msg=f'Modification time: {first_path} != {second_path}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
