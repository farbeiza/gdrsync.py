#!/usr/bin/python

import config

import logging

logging.basicConfig()
logging.getLogger().setLevel(config.PARSER.get('gdrsync', 'logLevel'))

import localfolder
import remotefolder

localFile = localfolder.Factory().create('/home/farbeiza/Escritorio')
remoteFile = remotefolder.Factory().create('/test')

print remoteFile.file.delegate
print remoteFile._files
print remoteFile._folders
