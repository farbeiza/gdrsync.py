#!/usr/bin/python

import config
import utils

import apiclient.discovery
import httplib2
import logging
import oauth2client.client
import re

TIMEOUT = 60 # seconds

FIELDS = 'id, title, mimeType, createdDate, modifiedDate, md5Checksum, fileSize, description, downloadUrl'

DEFAULT_CLIENT_ID = '387402765904.apps.googleusercontent.com'
DEFAULT_CLIENT_SECRET = 'WTj0xKbLAFjDqUeT2HGDZHCi'

OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

SEARCH_PARAMETER_RE = re.compile('(' + '[' + '\'\\\\' + ']' + ')')
SEARCH_PARAMETER_REPLACEMENT = '\\\\\\1'

LOGGER = logging.getLogger(__name__)

def escapeQueryParameter(parameter):
    return SEARCH_PARAMETER_RE.sub(SEARCH_PARAMETER_REPLACEMENT, parameter)

def drive(saveCredentials = None):
    http = (credentials(saveCredentials)
            .authorize(httplib2.Http(timeout = TIMEOUT)))

    return (apiclient.discovery.build('drive', 'v2', http = http),
            http)

def credentials(save = None):
    clientId = config.get('clientId')
    clientSecret = config.get('clientSecret')
    if not clientId:
        clientId = DEFAULT_CLIENT_ID
        clientSecret = DEFAULT_CLIENT_SECRET

    refreshToken = config.get('refreshToken')
    if refreshToken:
        LOGGER.debug('Using stored refresh token...')

        return oauth2client.client.OAuth2Credentials(None, clientId,
                clientSecret, refreshToken, None,
                oauth2client.GOOGLE_TOKEN_URI, None)

    flow = oauth2client.client.OAuth2WebServerFlow(clientId, clientSecret,
            OAUTH_SCOPE, REDIRECT_URI,
            access_type = 'offline', approval_prompt = 'force')

    url = flow.step1_get_authorize_url()
    print 'Please open the following URL: '
    print url
    authorizationCode = raw_input('Copy and paste the authorization code: ').strip()

    LOGGER.debug('Requesting new refresh token...')
    credentials = flow.step2_exchange(authorizationCode)

    refreshToken = credentials.refresh_token
    print 'Refresh token: ' + refreshToken

    if utils.firstNonNone(save, False):
        config.set('refreshToken', refreshToken)
        config.save()

    return credentials
