#!/usr/bin/python

import file
import utils

import posixpath

class Folder(object):
    def __init__(self, file, children = None, duplicate = None):
        # Never instantiate the base class.
        assert self.__class__ != Folder
        self._file = file
        self._children = utils.firstNonNone(children, {})
        self._duplicate = utils.firstNonNone(duplicate, [])

    def _newFolder(self, file, children = None, duplicate = None):
        return self.__class__(file, children, duplicate)

    def addChild(self, file):
        if file.name in self._children:
            self._duplicate.append(file)

            return self

        self._children[file.name] = file

        return self

    def addChildren(self, files):
        for file in files:
            self.addChild(file)

        return self

    @property
    def file(self):
        return self._file

    @property
    def children(self):
        return self._children

    @property
    def duplicate(self):
        return self._duplicate

    def files(self):
        return filter(lambda f: not f.folder, self._children.values())

    def folders(self):
        return filter(lambda f: f.folder, self._children.values())

    def withoutChildren(self):
        return self._newFolder(self._file)

    def withoutDuplicate(self):
        return self._newFolder(self._file, self._children)

    def createFile(self, name, folder = None):
        raise NotImplementedError()

import localfolder
import remotefolder

import urlparse

class Factory(object):
    class VirtualFile(file.File):
        def __init__(self):
            super(Factory.VirtualFile, self).__init__(None, None, True)

    class VirtualFolder(Folder):
        def __init__(self):
            super(Factory.VirtualFolder, self).__init__(Factory.VirtualFile())

    def __init__(self, context):
        self.remoteFolderFactory = remotefolder.Factory(context)
        self.localFolderFactory = localfolder.Factory(context)

    def createVirtual(self, paths):
        virtualFolder = Factory.VirtualFolder()
        for path in paths:
            (head, tail) = posixpath.split(path)
            if tail == '':
                pathFolder = self.createFromURL(head)
                virtualFolder.addChildren(pathFolder.children.values())
            else:
                realFolder = self.createFromURL(head)
                # Virtual folder are sources, so the file must already exist.
                virtualFolder.addChild(realFolder.children['tail'])

        return virtualFolder

    def createFromURL(self, url):
        parsed_url = urlparse.urlparse(url)
        if parsed_url.scheme == 'gdrive':
            return self.remoteFolderFactory.create(parsed_url.path)
        elif not parsed_url.scheme or parsed_url.scheme == 'file':
            return self.localFolderFactory.create(parsed_url.path)
        raise RuntimeError('Unable to handle url: %s' % file_descriptor)

    def create(self, file_descriptor):
        return self._getFactoryForFileDescriptor(
            file_descriptor).create(file_descriptor)

    def createEmpty(self, file_descriptor):
        return self._getFactoryForFileDescriptor(
            file_descriptor).createEmpty(file_descriptor)

    def _getFactoryForFileDescriptor(self, file_descriptor):
        assert isinstance(file_descriptor, file.File)
        return file_descriptor.select((self.localFolderFactory,
                                       self.remoteFolderFactory))
