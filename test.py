#!/usr/bin/python

import config

import logging

logging.basicConfig()
logging.getLogger().setLevel(config.PARSER.get('gdrsync', 'logLevel'))

import driveutils

import httplib2
import pprint

from apiclient.http import MediaFileUpload

# Path to the file to upload
FILENAME = '/home/farbeiza/Escritorio/surgeries.txt'

# Insert a file
media_body = MediaFileUpload(FILENAME, mimetype='text/plain', resumable=True)
body = {
  'title': 'My document',
  'description': 'A test document',
  'mimeType': 'text/plain'
}

file = driveutils.DRIVE_SERVICE.files().insert(body=body, media_body=media_body).execute()
pprint.pprint(file)

