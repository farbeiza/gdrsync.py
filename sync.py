#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import downloadmanager
import driveutils
import filter
import localcopymanager
import localfolder
import location
import remotecopymanager
import remotefolder
import summary
import uploadmanager

LOGGER = logging.getLogger(__name__)


class Sync(object):
    def __init__(self, args):
        self.args = args

        self.drive = driveutils.drive(updateCredentials=self.args.updateCredentials,
                                      ignoreCredentials=self.args.ignoreCredentials)

        self.sourceLocations = [location.create(url) for url in self.args.sourceUrls]
        self.destLocation = location.create(self.args.destUrl)

        self.sourceFolderFactory = self.folderFactoryFromLocations(self.sourceLocations)
        self.destFolderFactory = self.folderFactoryFromLocation(self.destLocation)

        self.summary = summary.Summary()

        self.transferManager = self.createTransferManager()

    def folderFactoryFromLocations(self, locations):
        for location in locations:
            return self.folderFactoryFromLocation(location)

    def folderFactoryFromLocation(self, location):
        if location.remote:
            return remotefolder.Factory(self.drive)

        return localfolder.Factory()

    def createTransferManager(self):
        if self.sourceFolderFactory.remote:
            if self.destFolderFactory.remote:
                return remotecopymanager.RemoteCopyManager(self.drive, self.summary)
            else:
                return downloadmanager.DownloadManager(self.drive, self.summary)
        else:
            if self.destFolderFactory.remote:
                return uploadmanager.UploadManager(self.drive, self.summary)
            else:
                return localcopymanager.LocalCopyManager(self.summary)

    def close(self):
        self.drive.close()

    def sync(self):
        LOGGER.info('Starting...')

        virtualSourceFolder = self.sourceFolderFactory.virtualFromLocations(self.sourceLocations)
        destFolder = self.destFolderFactory.create(self.destLocation, create_path=True)
        self._sync(virtualSourceFolder, destFolder)

        self.logResult()

        LOGGER.info('End.')

    def _sync(self, sourceFolder, destFolder):
        destFolder = self.trash(sourceFolder, destFolder)

        self.summary.addTotalFiles(len(sourceFolder.children))

        destFolder = self.syncFolder(sourceFolder, destFolder)

        if not self.args.recursive:
            return

        for sourceFile in sourceFolder.folders():
            if self.isExcluded(sourceFile):
                LOGGER.info('%s: Skipping excluded folder...', sourceFile)
                continue

            if (not self.args.copyLinks) and sourceFile.link:
                continue

            try:
                destFile = destFolder.children[sourceFile.location.name]
            except KeyError as error:
                LOGGER.warning('%s: Not found in destination folder: %s', sourceFile, destFolder)
                continue

            self._sync(self.createSourceFolder(sourceFile),
                       self.createDestFolder(destFile))

    def trash(self, sourceFolder, destFolder):
        destFolder = self.trashDuplicate(sourceFolder, destFolder)
        destFolder = self.trashExtraneous(sourceFolder, destFolder)
        destFolder = self.trashDifferentType(sourceFolder, destFolder)
        destFolder = self.trashExcluded(sourceFolder, destFolder)

        return destFolder

    def trashDuplicate(self, sourceFolder, destFolder):
        if not self.args.delete:
            return destFolder

        for destFile in destFolder.duplicate:
            LOGGER.debug('%s: Duplicate file.', destFile)

            destFile = self.trashFile(destFile)

        return destFolder.withoutDuplicate()

    def trashFile(self, destFile):
        LOGGER.info('%s: Trashing file...', destFile)
        if self.args.dryRun:
            return destFile

        return self.transferManager.remove(destFile)

    def trashExtraneous(self, sourceFolder, destFolder):
        if not self.args.delete:
            return destFolder

        output = destFolder.withoutChildren()
        for destFile in destFolder.children.values():
            if destFile.location.name in sourceFolder.children:
                output.addChild(destFile)
                continue

            LOGGER.debug('%s: Extraneous file.', destFile)

            destFile = self.trashFile(destFile)

        return output

    def trashDifferentType(self, sourceFolder, destFolder):
        if not self.args.delete:
            return destFolder

        output = destFolder.withoutChildren()
        for destFile in destFolder.children.values():
            sourceFile = sourceFolder.children[destFile.location.name]
            if sourceFile.folder == destFile.folder:
                output.addChild(destFile)
                continue

            LOGGER.debug('%s: Different type: %s != %s.', destFile,
                         sourceFile.folder, destFile.folder)

            destFile = self.trashFile(destFile)

        return output

    def trashExcluded(self, sourceFolder, destFolder):
        if not self.args.deleteExcluded:
            return destFolder

        output = destFolder.withoutChildren()
        for destFile in destFolder.children.values():
            sourceFile = sourceFolder.children[destFile.location.name]
            if not self.isExcluded(sourceFile):
                output.addChild(destFile)
                continue

            LOGGER.debug('%s: Excluded file.', destFile)

            destFile = self.trashFile(destFile)

        return output

    def isExcluded(self, file):
        return filter.isExcluded(self.args.filters, file)

    def syncFolder(self, sourceFolder, destFolder):
        output = (destFolder.withoutChildren()
                  .addChildren(destFolder.children.values()))
        for sourceFile in sourceFolder.children.values():
            self.summary.addCheckedFiles(1)
            self.summary.addCheckedSize(sourceFile.size)

            try:
                destFile = self.copy(sourceFile, destFolder)
                if destFile is None:
                    continue

                output.addChild(destFile)
            except FileNotFoundError as error:
                LOGGER.warning('%s: No such file or directory.', sourceFile)

        return output

    def copy(self, sourceFile, destFolder):
        destFile = destFolder.children.get(sourceFile.location.name)

        fileOperation = self.fileOperation(sourceFile, destFile)
        if fileOperation is None:
            return None

        if destFile is None:
            destFile = destFolder.createFile(sourceFile.location.name, folder=sourceFile.folder)

        return fileOperation(sourceFile, destFile)

    def fileOperation(self, sourceFile, destFile):
        if self.isExcluded(sourceFile):
            LOGGER.info('%s: Skipping excluded file... (Checked %d/%d files)', sourceFile,
                        self.summary.checkedFiles, self.summary.totalFiles)

            return None

        if (not self.args.copyLinks) and sourceFile.link:
            LOGGER.info('%s: Skipping non-regular file... (Checked %d/%d files)', sourceFile,
                        self.summary.checkedFiles, self.summary.totalFiles)

            return None

        if destFile is None:
            if sourceFile.folder:
                return self.insertFolder

            return self.insertFile

        if self.args.update and (destFile.modified > sourceFile.modified):
            LOGGER.debug('%s: Newer destination file: %s < %s.', destFile,
                         sourceFile.modified, destFile.modified)
        elif self.args.checksum:
            fileOperation = self.checkChecksum(sourceFile, destFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkSize(sourceFile, destFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkModified(sourceFile, destFile)
            if fileOperation is not None:
                return fileOperation
        else:
            fileOperation = self.checkSize(sourceFile, destFile)
            if fileOperation is not None:
                return fileOperation

            fileOperation = self.checkModified(sourceFile, destFile)
            if fileOperation is not None:
                return fileOperation

        LOGGER.debug('%s: Up to date. (Checked %d/%d files)', destFile,
                     self.summary.checkedFiles, self.summary.totalFiles)

        return None

    def checkChecksum(self, sourceFile, destFile):
        if destFile.md5 == sourceFile.md5:
            return None

        LOGGER.debug('%s: Different checksum: %s != %s.', destFile,
                     sourceFile.md5, destFile.md5)

        return self.updateFile

    def checkSize(self, sourceFile, destFile):
        if destFile.size == sourceFile.size:
            return None

        LOGGER.debug('%s: Different size: %d != %d.', destFile,
                     sourceFile.size, destFile.size)

        return self.updateFile

    def checkModified(self, sourceFile, destFile):
        if destFile.modified == sourceFile.modified:
            return None

        fileOperation = self.checkChecksum(sourceFile, destFile)
        if fileOperation is not None:
            return fileOperation

        LOGGER.debug('%s: Different modified time: %s != %s.', destFile,
                     sourceFile.modified, destFile.modified)

        return self.touch

    def insertFolder(self, sourceFile, destFile):
        LOGGER.info('%s: Inserting folder... (Checked %d/%d files)', destFile,
                    self.summary.checkedFiles, self.summary.totalFiles)
        if self.args.dryRun:
            return destFile

        return self.transferManager.insertFolder(sourceFile, destFile)

    def insertFile(self, sourceFile, destFile):
        LOGGER.info('%s: Inserting file... (Checked %d/%d files)', destFile,
                    self.summary.checkedFiles, self.summary.totalFiles)
        if self.args.dryRun:
            return destFile

        return self.transferManager.insertFile(sourceFile, destFile)

    def updateFile(self, sourceFile, destFile):
        LOGGER.info('%s: Updating file... (Checked %d/%d files)', destFile,
                    self.summary.checkedFiles, self.summary.totalFiles)
        if self.args.dryRun:
            return destFile

        return self.transferManager.updateFile(sourceFile, destFile)

    def touch(self, sourceFile, destFile):
        LOGGER.info('%s: Updating modified time... (Checked %d/%d files)', destFile,
                    self.summary.checkedFiles, self.summary.totalFiles)
        if self.args.dryRun:
            return destFile

        return self.transferManager.touch(sourceFile, destFile)

    def createSourceFolder(self, sourceFile):
        return self.sourceFolderFactory.create(sourceFile)

    def createDestFolder(self, destFile):
        if not destFile.exists:
            return self.destFolderFactory.empty(destFile)

        return self.destFolderFactory.create(destFile)

    def logResult(self):
        copiedSize = self.summary.copiedSize
        copiedTime = round(self.summary.copiedTime)
        bS = self.summary.bS

        checkedSize = self.summary.checkedSize

        LOGGER.info('Copied %d files (%d%s / %ds = %d%s) Checked %d files (%d%s)',
                    self.summary.copiedFiles,
                    copiedSize.value, copiedSize.unit, copiedTime,
                    bS.value, bS.unit,
                    self.summary.checkedFiles, checkedSize.value, checkedSize.unit)
