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

import synctestcase

logging.basicConfig(level=logging.INFO)


class UpdateTestCase(synctestcase.SyncTestCase):
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
