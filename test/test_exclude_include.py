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


class ExcludeIncludeTestCase(synctestcase.SyncTestCase):
    def test_should_not_create_folder_when_exclude_with_pattern(self):
        self.exclude_include_folder_test('excluded_folder', 'included_folder',
                                         additional_args=['--exclude', 'excluded*'])

    def test_should_not_create_folder_when_exclude_with_regex(self):
        self.exclude_include_folder_test('excluded_folder', 'included_folder',
                                         additional_args=['--rexclude', 'excluded.*$'])

    def test_should_create_folder_when_include_before_exclude_with_pattern(self):
        self.exclude_include_folder_test('excluded_folder', 'excluded_not_folder',
                                         additional_args=['--include', 'excluded_not*',
                                                          '--exclude', 'excluded*'])

    def test_should_create_folder_when_include_before_exclude_with_regex(self):
        self.exclude_include_folder_test('excluded_folder', 'excluded_not_folder',
                                         additional_args=['--rinclude', 'excluded_not.*$',
                                                          '--rexclude', 'excluded.*$'])

    def exclude_include_folder_test(self, excluded_folder_name, included_folder_name, additional_args):
        file_name = 'file'
        with tempfile.TemporaryDirectory() as expected_path:
            expected_excluded_folder_path = os.path.join(expected_path, excluded_folder_name)
            expected_excluded_file_path = os.path.join(expected_excluded_folder_path, file_name)

            os.mkdir(expected_excluded_folder_path)
            self.file_write_random_line(expected_excluded_file_path)

            expected_included_folder_path = os.path.join(expected_path, included_folder_name)
            expected_included_file_path = os.path.join(expected_included_folder_path, file_name)

            os.mkdir(expected_included_folder_path)
            self.file_write_random_line(expected_included_file_path)

            self.sync_from_local(expected_path, additional_args=additional_args)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFolderMatches(actual_path, expected_path, name=included_folder_name)
                actual_included_folder_path = os.path.join(actual_path, included_folder_name)
                self.assertFileMatches(actual_included_folder_path, expected_included_folder_path, name=file_name)

                self.assertFolder(expected_excluded_folder_path)
                actual_excluded_folder_path = os.path.join(actual_path, excluded_folder_name)
                self.assertFolderNotFound(actual_excluded_folder_path)

    def test_should_not_create_file_when_exclude_with_pattern(self):
        self.exclude_include_file_test('excluded_file', 'included_file',
                                       additional_args=['--exclude', 'excluded*'])

    def test_should_not_create_file_when_exclude_with_regex(self):
        self.exclude_include_file_test('excluded_file', 'included_file',
                                       additional_args=['--rexclude', 'excluded.*$'])

    def test_should_create_file_when_include_before_exclude_with_pattern(self):
        self.exclude_include_file_test('excluded_file', 'excluded_not_file',
                                       additional_args=['--include', 'excluded_not*',
                                                        '--exclude', 'excluded*'])

    def test_should_create_file_when_include_before_exclude_with_regex(self):
        self.exclude_include_file_test('excluded_file', 'excluded_not_file',
                                       additional_args=['--rinclude', 'excluded_not.*$',
                                                        '--rexclude', 'excluded.*$'])

    def exclude_include_file_test(self, excluded_file_name, included_file_name, additional_args):
        with tempfile.TemporaryDirectory() as expected_path:
            expected_excluded_file_path = os.path.join(expected_path, excluded_file_name)
            self.file_write_random_line(expected_excluded_file_path)

            expected_included_file_path = os.path.join(expected_path, included_file_name)
            self.file_write_random_line(expected_included_file_path)

            self.sync_from_local(expected_path, additional_args=additional_args)

            with tempfile.TemporaryDirectory() as actual_path:
                self.sync_from_remote(actual_path)

                self.assertFileMatches(actual_path, expected_path, name=included_file_name)

                self.assertFile(expected_excluded_file_path)
                actual_excluded_file_path = os.path.join(actual_path, excluded_file_name)
                self.assertFileNotFound(actual_excluded_file_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
