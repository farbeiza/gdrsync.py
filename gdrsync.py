#!/usr/bin/python

import config

import logging

logging.basicConfig()
logging.getLogger().setLevel(config.PARSER.get('gdrsync', 'logLevel'))

import remotefile

remoteFile = remotefile.Factory().create('/test')

print remoteFile.delegate
