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
import os
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

    def assertLink(self, path):
        self.assertTrue(os.path.lexists(path), msg=f'Symbolic link does not exist: {path}')
        self.assertTrue(os.path.islink(path), msg=f'Not a symbolic link: {path}')

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
