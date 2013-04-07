#!/usr/bin/python

import config
import utils

import apiclient.discovery
import calendar
import datetime
import httplib2
import logging
import oauth2client.client
import re
import time

TIMEOUT = 60 # seconds

DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

FIELDS = 'id, title, mimeType, modifiedDate, md5Checksum, fileSize'

CLIENT_ID = '387402765904.apps.googleusercontent.com'
CLIENT_SECRET = 'WTj0xKbLAFjDqUeT2HGDZHCi'

OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

SEARCH_PARAMETER_RE = re.compile('(' + '[' + '\'\\\\' + ']' + ')')
SEARCH_PARAMETER_REPLACEMENT = '\\\\\\1'

LOGGER = logging.getLogger(__name__)

def formatTime(seconds):
    dateTime = datetime.datetime.utcfromtimestamp(seconds)
    return dateTime.strftime(DATE_TIME_FORMAT)

def parseTime(string):
    dateTime = datetime.datetime.strptime(string, DATE_TIME_FORMAT)

    return (calendar.timegm(dateTime.timetuple())
            + (dateTime.microsecond / utils.US))

def credentials():
    refreshToken = config.PARSER.get('gdrsync', 'refreshToken')
    if refreshToken:
        LOGGER.debug('Using stored refresh token...')

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

    LOGGER.debug('Requesting new refresh token...')
    credentials = flow.step2_exchange(authorizationCode)
    print 'Refresh token: ' + credentials.refresh_token

    return credentials

http = credentials().authorize(httplib2.Http(timeout = TIMEOUT))

DRIVE = apiclient.discovery.build('drive', 'v2', http = http)

def escapeQueryParameter(parameter):
    return SEARCH_PARAMETER_RE.sub(SEARCH_PARAMETER_REPLACEMENT, parameter)
