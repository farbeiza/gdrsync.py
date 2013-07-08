#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append('%s/..' % sys.path[0])

import drivemock
import localfolder
import folder
import remotefolder

import os
import unittest

class TestFolder(unittest.TestCase):

    def test_folder_factory(self):
        os.chdir('%s/..' % sys.path[0])
        drive = drivemock.DriveMock()
        context = lambda: None
        context.drive = drive

        factory = folder.Factory(context)
        self.assertIsInstance(factory.createFromURL('gdrive:///tmp'), remotefolder.RemoteFolder)
        self.assertIsInstance(factory.createFromURL('file:///tmp'), localfolder.LocalFolder)
        self.assertIsInstance(factory.createFromURL('/tmp'), localfolder.LocalFolder)
        self.assertIsInstance(factory.createFromURL('test'), localfolder.LocalFolder)

if __name__ == '__main__':
    unittest.main()
