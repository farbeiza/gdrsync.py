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
import re

import filter
import pattern

PARSER = argparse.ArgumentParser(description='Copy files between a local system' ' and a Google drive repository.',
                                 epilog='Source and destination URLs may be local or remote. '
                                        ' Local URLs: URLs with the form file:///path'
                                        ' or file://host/path or native path names.'
                                        ' Remote URLs: A URL with the form gdrive:///path,'
                                        ' gdrive://host/path or gdrive:/path.')

NATIVE_TRAILING_MESSAGE = ''
if os.path.sep != '/':
    NATIVE_TRAILING_MESSAGE = ' (or %s, if a local native path name)' % os.path.sep

PARSER.add_argument('sourceUrls', nargs='+',
                    help=('source URLs.'
                          ' A trailing /%s means "copy the contents of this directory",'
                          ' as opposed to "copy the directory itself".'
                          % NATIVE_TRAILING_MESSAGE),
                    metavar='SOURCE')
PARSER.add_argument('destUrl', help='destination URL', metavar='DEST')

PARSER.add_argument('-c', '--checksum', action='store_true',
                    help='skip based on checksum, not mod-time & size')
PARSER.add_argument('-L', '--copy-links', action='store_true', dest='copyLinks',
                    help='transform symlink into referent file/dir')
PARSER.add_argument('--delete', action='store_true',
                    help='delete duplicate and extraneous files from dest dirs')
PARSER.add_argument('--delete-excluded', action='store_true', dest='deleteExcluded',
                    help='also delete excluded files from dest dirs')


class FilterAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")

        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        filters = getattr(namespace, self.dest, [])
        if filters is None:
            filters = []

        filter = self.filter(values)
        filters.append(filter)

        setattr(namespace, self.dest, filters)

    def filter(self, value):
        raise NotImplementedError()


class ExcludeAction(FilterAction):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def filter(self, value):
        return pattern.filter(value, filter.Exclude)


class IncludeAction(FilterAction):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def filter(self, value):
        return pattern.filter(value, filter.Include)


class RegexExcludeAction(FilterAction):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def filter(self, value):
        regex = re.compile(value)
        return filter.Exclude(regex)


class RegexIncludeAction(FilterAction):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def filter(self, value):
        regex = re.compile(value)
        return filter.Include(regex)


PARSER.add_argument('--exclude', action=ExcludeAction, dest='filters',
                    help='exclude files matching PATTERN', metavar='PATTERN')
PARSER.add_argument('--include', action=IncludeAction, dest='filters',
                    help='don\'t exclude files matching PATTERN', metavar='PATTERN')
PARSER.add_argument('--rexclude', action=RegexExcludeAction, dest='filters',
                    help='exclude files matching REGEX', metavar='REGEX')
PARSER.add_argument('--rinclude', action=RegexIncludeAction, dest='filters',
                    help='don\'t exclude files matching REGEX', metavar='REGEX')

PARSER.add_argument('-n', '--dry-run', action='store_true', dest='dryRun',
                    help='perform a trial run with no changes made')
PARSER.add_argument('-r', '--recursive', action='store_true',
                    help='recurse into directories')
PARSER.add_argument('-p', '--update-credentials', action='store_true', dest='updateCredentials',
                    help='update credentials')
PARSER.add_argument('-P', '--ignore-credentials', action='store_true', dest='ignoreCredentials',
                    help='ignore existing credentials')
PARSER.add_argument('-u', '--update', action='store_true',
                    help='skip files that are newer on the receiver')
PARSER.add_argument('-v', '--verbose', action='count', default=0, dest='verbosity',
                    help='increase verbosity')

ARGS = PARSER.parse_args()

import logging

LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]
LOG_LEVEL = LOG_LEVELS[min(ARGS.verbosity, len(LOG_LEVELS) - 1)]

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(name)s: %(message)s',
                    level=LOG_LEVEL)
if ARGS.verbosity < len(LOG_LEVELS):
    logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)

import downloadmanager
import driveutils
import localcopymanager
import localfolder
import location
import remotecopymanager
import remotefolder
import summary
import uploadmanager

LOGGER = logging.getLogger(__name__)


class GdrSync(object):
    def __init__(self, args):
        self.args = args

        drive = driveutils.drive(updateCredentials=self.args.updateCredentials,
                                 ignoreCredentials=self.args.ignoreCredentials)

        self.sourceLocations = [location.create(url) for url in self.args.sourceUrls]
        self.destLocation = location.create(self.args.destUrl)

        self.sourceFolderFactory = self.folderFactoryFromLocations(self.sourceLocations, drive)
        self.destFolderFactory = self.folderFactoryFromLocation(self.destLocation, drive)

        self.summary = summary.Summary()

        self.transferManager = self.createTransferManager(drive)

    def folderFactoryFromLocations(self, locations, drive):
        for location in locations:
            return self.folderFactoryFromLocation(location, drive)

    def folderFactoryFromLocation(self, location, drive):
        if location.remote:
            return remotefolder.Factory(drive)

        return localfolder.Factory()

    def createTransferManager(self, drive):
        if self.sourceFolderFactory.remote:
            if self.destFolderFactory.remote:
                return remotecopymanager.RemoteCopyManager(drive, self.summary)
            else:
                return downloadmanager.DownloadManager(drive, self.summary)
        else:
            if self.destFolderFactory.remote:
                return uploadmanager.UploadManager(drive, self.summary)
            else:
                return localcopymanager.LocalCopyManager(self.summary)

    def sync(self):
        LOGGER.info('Starting...')

        virtualSourceFolder = self.sourceFolderFactory.virtualFromLocations(self.sourceLocations)
        destFolder = self.destFolderFactory.create(self.destLocation)
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
            except KeyError:
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
            destFile = destFolder.createFile(sourceFile.location.name, sourceFile.folder)

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


if __name__ == '__main__':
    GdrSync(ARGS).sync()
