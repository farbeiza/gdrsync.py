#!/usr/bin/python

import file

class VirtualFile(file.File):
    def __init__(self, folder = None):
        super(VirtualFile, self).__init__(None, None, folder)
