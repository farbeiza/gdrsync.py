#!/usr/bin/python

import re

import httplib2

import apiclient.discovery
import oauth2client.client

FIELDS = 'id, title, mimeType, modifiedDate, md5Checksum, fileSize'

MIME_FOLDER = 'application/vnd.google-apps.folder'

SEARCH_PARAMETER_RE = re.compile('(' + '[' + '\'\\\\' + ']' + ')')
SEARCH_PARAMETER_REPLACEMENT = '\\\\\\1'

CLIENT_ID = '387402765904.apps.googleusercontent.com'
CLIENT_SECRET = 'WTj0xKbLAFjDqUeT2HGDZHCi'

OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

def escapeQueryParameter(parameter):
    return SEARCH_PARAMETER_RE.sub(SEARCH_PARAMETER_REPLACEMENT, parameter)

flow = oauth2client.client.OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET,
        OAUTH_SCOPE, REDIRECT_URI)

url = flow.step1_get_authorize_url()
print 'Please open the following URL: '
print url
authorizationCode = raw_input('Copy and paste the authorization code: ').strip()

credentials = flow.step2_exchange(authorizationCode)

http = httplib2.Http()
http = credentials.authorize(http)

DRIVE_SERVICE = apiclient.discovery.build('drive', 'v2', http = http)
