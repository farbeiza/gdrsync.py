#!/usr/bin/python

import file
import utils

import date
import hashlib
import os
import stat

MD5_BUFFER_SIZE = 16 * utils.KIB

def fromParent(parent, path, folder = None):
    return fromParentPath(parent.context, parent.path, path, folder)

def fromParentPath(context, parentPath, path, folder = None):
    name = os.path.basename(path)
    path = os.path.join(parentPath, name)

    return LocalFile(context, path, folder)

class LocalFile(file.File):
    def __init__(self, context, path, folder = None):
        path = unicode(path)
        name = os.path.basename(path)
        folder = utils.firstNonNone(folder, os.path.isdir(path) and
                                            not os.path.islink(path))

        super(LocalFile, self).__init__(path, name, folder)
        self._content_md5 = None
        self.context = context

    @property
    def contentSize(self):
        if not self.exists or self.link or self.folder:
            return 0

        return os.path.getsize(self.path)

    @property
    def modified(self):
        file_stat = os.lstat(self.path)
        return date.fromSeconds(file_stat.st_mtime)

    @property
    def contentMd5(self):
        if self._content_md5 is None:
            md5 = hashlib.md5()
            if self.contentSize > 0:
                with open(self.path, mode = 'rb') as file:
                    while True:
                        data = file.read(MD5_BUFFER_SIZE)
                        if not data:
                            break

                        md5.update(data)

            self._content_md5 = md5.hexdigest()
        return self._content_md5

    @property
    def exists(self):
        return os.path.lexists(self.path)

    @property
    def link(self):
        return os.path.islink(self.path)

    def metadata(self, withMd5 = False):
        file_stat = os.lstat(self.path)
        metadata = {
            'uid': file_stat.st_uid,
            'gid': file_stat.st_gid,
            'fileSize': self.contentSize
        }
        if self.link:
            metadata['target'] = os.readlink(self.path).encode('utf-8')
            metadata['type'] = 'link'
        else:
            if not self.folder:
                metadata['modifiedDate'] = str(self.modified)
            metadata['mode'] = stat.S_IMODE(file_stat.st_mode)
        if withMd5:
            metadata['cs'] = self.md5
        return metadata

    def select(self, tuple):
        return tuple[0]

class Factory(object):
    def __init__(self, context):
        self.context = context

    def create(self, context, path):
        if not os.path.lexists(path):
            raise RuntimeError('%s not found' % path)

        return LocalFile(context, path)
