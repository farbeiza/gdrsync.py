#!/usr/bin/python

import config

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

def credentials():
    refreshToken = config.PARSER.get('gdrsync', 'refreshToken')
    if refreshToken:
        return oauth2client.client.OAuth2Credentials(None, CLIENT_ID,
                CLIENT_SECRET, refreshToken, None,
                oauth2client.GOOGLE_TOKEN_URI, None)

    flow = oauth2client.client.OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET,
            OAUTH_SCOPE, REDIRECT_URI,
            access_type = 'offline', approval_prompt = 'force')

    url = flow.step1_get_authorize_url()
    print 'Please open the following URL: '
    print url
    authorizationCode = raw_input('Copy and paste the authorization code: ').strip()

    credentials = flow.step2_exchange(authorizationCode)
    print "Refresh token: " + credentials.refresh_token

    return credentials

http = credentials().authorize(httplib2.Http())

DRIVE_SERVICE = apiclient.discovery.build('drive', 'v2', http = http)
