#!/usr/bin/python

import hashlib
import os

class LocalFile:
    MD5_BUFFER_SIZE = 16 * 1024

    def __init__(self, pathname):
        self.pathname = pathname

    @property
    def delegate(self):
        return self.pathname

    @property
    def path(self):
        return self.pathname

    @property
    def name(self):
        return os.path.basename(self.pathname)

    @property
    def size(self):
        return os.path.getsize(self.pathname)

    @property
    def modified(self):
        return os.path.getmtime(self.pathname)

    @property
    def md5(self):
        with open(self.pathname, mode = 'rb') as file:
            md5 = hashlib.md5()
            while True:
                data = file.read(LocalFile.MD5_BUFFER_SIZE)
                if not data:
                    break

                md5.update(data)

        return md5.hexdigest()

    @property
    def folder(self):
        return os.path.isdir(self.pathname)
