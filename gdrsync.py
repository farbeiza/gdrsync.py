#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import argparse
import os.path

parser = argparse.ArgumentParser(description = 'Copy files between a local system'
                                 ' and a Google drive repository.',
                                 epilog = 'Source and destination URLs may be local or remote. '
                                 ' Local URLs: URLs with the form file:///path'
                                 ' or file://host/path or native path names.'
                                 ' Remote URLs: A URL with the form gdrive:///path'
                                 ' or gdrive://host/path.')

nativeTrailingMessage = ''
if os.path.sep != '/':
    nativeTrailingMessage = ' (or %s, if a local native path name)' % os.path.sep

parser.add_argument('sourceUrls', nargs='+',
        help = ('source URLs.'
                ' A trailing /%s means "copy the contents of this directory",'
                ' as opposed to "copy the directory itself".'
                % nativeTrailingMessage),
        metavar = 'SOURCE')
parser.add_argument('destUrl', help = 'destination URL', metavar = 'DEST')

parser.add_argument('-c', '--checksum', action = 'store_true',
        help = 'skip based on checksum, not mod-time & size')
parser.add_argument('--delete', action = 'store_true',
        help = 'delete duplicate and extraneous files from dest dirs')
parser.add_argument('--delete-excluded', action = 'store_true',
        help = 'also delete excluded files from dest dirs',
        dest = 'deleteExcluded')
parser.add_argument('--rexclude', action = 'append',
        help = 'exclude files matching REGEX', metavar = 'REGEX')
parser.add_argument('-L', '--copy-links', action = 'store_true',
        help = 'transform symlink into referent file/dir', dest = 'copyLinks')
parser.add_argument('-n', '--dry-run', action = 'store_true',
        help = 'perform a trial run with no changes made', dest = 'dryRun')
parser.add_argument('-r', '--recursive', action = 'store_true',
        help = 'recurse into directories')
parser.add_argument('-S', '--save-credentials', action = 'store_true',
        help = 'save credentials for future re-use', dest = 'saveCredentials')
parser.add_argument('-u', '--update', action = 'store_true',
        help = 'skip files that are newer on the receiver')
parser.add_argument('-v', '--verbose', action='count', default = 0,
        help = 'increase verbosity', dest = 'verbosity')

args = parser.parse_args()

import logging

LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]
LOG_LEVEL = LOG_LEVELS[min(args.verbosity, len(LOG_LEVELS) - 1)]

logging.basicConfig(format = '%(asctime)s: %(levelname)s: %(name)s: %(message)s',
        level = LOG_LEVEL)
if args.verbosity < len(LOG_LEVELS):
    logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)
    logging.getLogger('oauth2client.client').setLevel(logging.ERROR)

import binaryunit
import downloadmanager
import driveutils
import folder
import localcopymanager
import localfolder
import remotecopymanager
import remotefolder
import summary
import uploadmanager

import errno
import re

LOGGER = logging.getLogger(__name__)

class GDRsync(object):
    def __init__(self, args):
        self.args = args

        self.exclude = self._exclude(self.args.rexclude)

        drive = driveutils.drive(self.args.saveCredentials)

        self.sourceFolderFactory = self.folderFactoryFromUrls(self.args.sourceUrls, drive)
        self.destFolderFactory = self.folderFactoryFromUrl(self.args.destUrl, drive)

        self.summary = summary.Summary()

        self.transferManager = self.createTransferManager(drive)

    def _exclude(self, excludeRes):
        if excludeRes is None:
            return []

        return [re.compile(exclude) for exclude in excludeRes]

    def folderFactoryFromUrls(self, urls, drive):
        for url in urls:
            return self.folderFactoryFromUrl(url, drive)

    def folderFactoryFromUrl(self, url, drive):
        folderFactory = remotefolder.Factory(drive)
        if folderFactory.handlesUrl(url):
            return folderFactory

        folderFactory = localfolder.Factory()
        if folderFactory.handlesUrl(url):
            return folderFactory

        raise RuntimeError('Unknown URL type: %s' % url)

    def createTransferManager(self, drive):
        if self.sourceFolderFactory.isRemote():
            if self.destFolderFactory.isRemote():
                return remotecopymanager.RemoteCopyManager(drive, self.summary)
            else:
                return downloadmanager.DownloadManager(drive, self.summary)
        else:
            if self.destFolderFactory.isRemote():
                return uploadmanager.UploadManager(drive, self.summary)
            else:
                return localcopymanager.LocalCopyManager(self.summary)

    def sync(self):
        LOGGER.info('Starting...')

        virtualSourceFolder = self.sourceFolderFactory.virtualFromUrls(self.args.sourceUrls)
        destFolder = self.destFolderFactory.fromUrl(self.args.destUrl)
        self._sync(virtualSourceFolder, destFolder)

        self.logResult();

        LOGGER.info('End.')

    def _sync(self, sourceFolder, destFolder):
        destFolder = self.trash(sourceFolder, destFolder)

        self.summary.addTotalFiles(len(sourceFolder.children))

        destFolder = self.syncFolder(sourceFolder, destFolder)

        if not self.args.recursive:
            return

        for sourceFile in sourceFolder.folders():
            if self.isExcluded(sourceFile):
                LOGGER.info('%s: Skipping excluded folder...', sourceFile.path)
                continue

            if (not self.args.copyLinks) and sourceFile.link:
                continue

            destFile = destFolder.children[sourceFile.name]

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
            LOGGER.debug('%s: Duplicate file.', destFile.path)

            destFile = self.trashFile(destFile)

        return destFolder.withoutDuplicate()

    def trashFile(self, destFile):
        LOGGER.info('%s: Trashing file...', destFile.path)
        if self.args.dryRun:
            return destFile

        return self.transferManager.remove(destFile)

    def trashExtraneous(self, sourceFolder, destFolder):
        if not self.args.delete:
            return destFolder

        output = destFolder.withoutChildren()
        for destFile in destFolder.children.values():
            if destFile.name in sourceFolder.children:
                output.addChild(destFile)
                continue

            LOGGER.debug('%s: Extraneous file.', destFile.path)

            destFile = self.trashFile(destFile)

        return output

    def trashDifferentType(self, sourceFolder, destFolder):
        if not self.args.delete:
            return destFolder

        output = destFolder.withoutChildren()
        for destFile in destFolder.children.values():
            sourceFile = sourceFolder.children[destFile.name]
            if sourceFile.folder == destFile.folder:
                output.addChild(destFile)
                continue

            LOGGER.debug('%s: Different type: %s != %s.', destFile.path,
                    sourceFile.folder, destFile.folder)

            destFile = self.trashFile(destFile)

        return output

    def trashExcluded(self, sourceFolder, destFolder):
        if not self.args.deleteExcluded:
            return destFolder

        output = destFolder.withoutChildren()
        for destFile in destFolder.children.values():
            sourceFile = sourceFolder.children[destFile.name]
            if not self.isExcluded(sourceFile):
                output.addChild(destFile)
                continue

            LOGGER.debug('%s: Excluded file.', destFile.path)

            destFile = self.trashFile(destFile)

        return output

    def isExcluded(self, sourceFile):
        if sourceFile.path is None:
            return False

        return any(re.match(sourceFile.path) for re in self.exclude)

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
                LOGGER.warn('%s: No such file or directory.', sourceFile.path)

        return output

    def copy(self, sourceFile, destFolder):
        destFile = destFolder.children.get(sourceFile.name)

        fileOperation = self.fileOperation(sourceFile, destFile)
        if fileOperation is None:
            return None

        if destFile is None:
            destFile = destFolder.createFile(sourceFile.name, sourceFile.folder)

        return fileOperation(sourceFile, destFile)

    def fileOperation(self, sourceFile, destFile):
        if self.isExcluded(sourceFile):
            LOGGER.info('%s: Skipping excluded file... (Checked %d/%d files)',
                    sourceFile.path, self.summary.checkedFiles, self.summary.totalFiles)

            return None

        if (not self.args.copyLinks) and sourceFile.link:
            LOGGER.info('%s: Skipping non-regular file... (Checked %d/%d files)',
                    sourceFile.path, self.summary.checkedFiles, self.summary.totalFiles)

            return None

        if destFile is None:
            if sourceFile.folder:
                return self.insertFolder

            return self.insertFile

        if self.args.update and (destFile.modified > sourceFile.modified):
            LOGGER.debug('%s: Newer destination file: %s < %s.',
                    destFile.path, sourceFile.modified, destFile.modified)
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

        LOGGER.debug('%s: Up to date. (Checked %d/%d files)', destFile.path,
                self.summary.checkedFiles, self.summary.totalFiles)

        return None

    def checkChecksum(self, sourceFile, destFile):
        if destFile.md5 == sourceFile.md5:
            return None

        LOGGER.debug('%s: Different checksum: %s != %s.', destFile.path,
                sourceFile.md5, destFile.md5)

        return self.updateFile

    def checkSize(self, sourceFile, destFile):
        if destFile.size == sourceFile.size:
            return None

        LOGGER.debug('%s: Different size: %d != %d.', destFile.path,
                sourceFile.size, destFile.size)

        return self.updateFile

    def checkModified(self, sourceFile, destFile):
        if destFile.modified == sourceFile.modified:
            return None

        fileOperation = self.checkChecksum(sourceFile, destFile)
        if fileOperation is not None:
            return fileOperation

        LOGGER.debug('%s: Different modified time: %s != %s.', destFile.path,
                sourceFile.modified, destFile.modified)

        return self.touch

    def insertFolder(self, sourceFile, destFile):
        LOGGER.info('%s: Inserting folder... (Checked %d/%d files)',
                destFile.path, self.summary.checkedFiles, self.summary.totalFiles)
        if self.args.dryRun:
            return destFile

        return self.transferManager.insertFolder(sourceFile, destFile)

    def insertFile(self, sourceFile, destFile):
        LOGGER.info('%s: Inserting file... (Checked %d/%d files)',
                destFile.path, self.summary.checkedFiles, self.summary.totalFiles)
        if self.args.dryRun:
            return destFile

        return self.transferManager.insertFile(sourceFile, destFile)

    def updateFile(self, sourceFile, destFile):
        LOGGER.info('%s: Updating file... (Checked %d/%d files)',
                destFile.path, self.summary.checkedFiles, self.summary.totalFiles)
        if self.args.dryRun:
            return destFile

        return self.transferManager.updateFile(sourceFile, destFile)

    def touch(self, sourceFile, destFile):
        LOGGER.info('%s: Updating modified date... (Checked %d/%d files)',
                destFile.path, self.summary.checkedFiles, self.summary.totalFiles)
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

GDRsync(args).sync()
