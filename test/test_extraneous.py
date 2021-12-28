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

import logging
import os.path
import shutil
import tempfile
import unittest

import synctestcase

logging.basicConfig(level=logging.INFO)


class ExtraneousTestCase(synctestcase.SyncTestCase):
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
