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
import tempfile
import unittest

import synctestcase

logging.basicConfig(level=logging.INFO)


class SymbolicLinkTestCase(synctestcase.SyncTestCase):
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
                self.assertLink(expected_link_path)
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

                actual_link_path = os.path.join(actual_path, link_name)
                self.assertLink(expected_link_path)
                self.assertFolder(actual_link_path)
                self.assertFolderMatches(actual_link_path, expected_folder_path)

                actual_link_file_path = os.path.join(actual_path, link_name, file_name)
                self.assertFileMatches(actual_link_file_path, expected_file_path)

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

                actual_link_path = os.path.join(actual_path, link_name)
                self.assertLink(expected_link_path)
                self.assertFileMatches(actual_link_path, expected_file_path)

    def test_should_not_create_symbolic_broken_link_when_option(self):
        missing_file_name = 'missing'
        link_name = 'link'
        with tempfile.TemporaryDirectory() as expected_path:
            missing_file_path = os.path.join(expected_path, missing_file_name)
            self.file_write_random_line(missing_file_path)

            expected_link_path = os.path.join(expected_path, link_name)
            os.symlink(missing_file_path, expected_link_path)

            os.remove(missing_file_path)

            self.sync_from_local(expected_path, additional_args=['-L'])

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFileNotFound(missing_file_path)
                self.assertLink(expected_link_path)

                actual_link_path = os.path.join(expected_path, link_name)
                self.assertFileNotFound(actual_link_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
