#!/usr/bin/python

import folder
import virtualfile

class Factory(object):
    def fromUrls(self, urls):
        return self.create([self.url2path(url) for url in urls])

    def url2path(self, urlString):
        raise NotImplementedError()

    def create(self, paths):
        virtualFolder = folder.Folder(virtualfile.VirtualFile(True))
        for path in paths:
            (head, tail) = self.split(path)
            if tail == '':
                pathFolder = self.folderFactory.create(head)
                virtualFolder.addChildren(pathFolder.children.values())
            else:
                pathFile = self.fileFactory.create(path)
                virtualFolder.addChild(pathFile)

        return virtualFolder

    def split(self, path):
        raise NotImplementedError()

    @property
    def folderFactory(self):
        raise NotImplementedError()

    @property
    def fileFactory(self):
        raise NotImplementedError()
