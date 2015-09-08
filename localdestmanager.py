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

import transfermanager

import os
import shutil

class LocalDestManager(transfermanager.TransferManager):
    def insertFolder(self, sourceFile, destinationFile):
        os.mkdir(destinationFile.path)

        return self.touch(sourceFile, destinationFile)

    def remove(self, destinationFile):
        if destinationFile.folder:
            shutil.rmtree(destinationFile.path)
        else:
            os.remove(destinationFile.path)

        return destinationFile.copy()

    def touch(self, sourceFile, destinationFile):
        os.utime(destinationFile.path,
                 times = (sourceFile.modified.seconds, sourceFile.modified.seconds))

        return destinationFile.copy()
