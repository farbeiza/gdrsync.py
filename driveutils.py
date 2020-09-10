#!/usr/bin/python
#
# Copyright 2015 Fernando Arbeiza <fernando.arbeiza@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import config
import utils

import googleapiclient.discovery
import google.oauth2.credentials
import google.auth.transport.requests
import google_auth_oauthlib.flow
import httplib2
import logging
import pickle
import os
import re

TIMEOUT = 60 # seconds

FIELDS = 'id, name, mimeType, createdTime, modifiedTime, parents, md5Checksum, size'

CREDENTIALS_FILE_NAME = 'credentials.pickle'
CREDENTIALS_FILE = os.path.join(config.CONFIG_DIR, CREDENTIALS_FILE_NAME)

DEFAULT_CLIENT_ID = '387402765904-b19a09e8o0gb7ote7vpcaca2f98pdj5m.apps.googleusercontent.com'
DEFAULT_CLIENT_SECRET = 'Eqzhho1ITDvOl2R5Yg49sgWt'

OAUTH_SCOPES = ['https://www.googleapis.com/auth/drive']
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

SEARCH_PARAMETER_RE = re.compile('(' + '[' + '\'\\\\' + ']' + ')')
SEARCH_PARAMETER_REPLACEMENT = '\\\\\\1'

LOGGER = logging.getLogger(__name__)

def escapeQueryParameter(parameter):
    return SEARCH_PARAMETER_RE.sub(SEARCH_PARAMETER_REPLACEMENT, parameter)

def drive(updateCredentials = False, ignoreCredentials = False):
    credentials = createCredentials(updateCredentials = updateCredentials,
                                    ignoreCredentials = ignoreCredentials)

    return googleapiclient.discovery.build('drive', 'v3', credentials = credentials,
                                           cache_discovery = False)

def createCredentials(updateCredentials = False, ignoreCredentials = False):
    clientId = config.get('clientId')
    clientSecret = config.get('clientSecret')
    if not clientId:
        clientId = DEFAULT_CLIENT_ID
        clientSecret = DEFAULT_CLIENT_SECRET

    credentials = None
    if (not updateCredentials) or ignoreCredentials:
        if os.path.exists(CREDENTIALS_FILE):
            LOGGER.debug('Loading credentials...')
            with open(CREDENTIALS_FILE, 'rb') as file:
                credentials = pickle.load(file)

    if (not credentials) or (not credentials.valid):
        if credentials and credentials.expired and credentials.refresh_token:
            LOGGER.debug('Using stored refresh token...')
            credentials.refresh(google.auth.transport.requests.Request())
        else:
            LOGGER.debug('Starting authentication flow...')
            client_config = {
                "installed": {
                    "client_id": clientId,
                    "client_secret": clientSecret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = (google_auth_oauthlib.flow.InstalledAppFlow
                    .from_client_config(client_config, OAUTH_SCOPES))
            credentials = flow.run_local_server(port = 0)

        if not ignoreCredentials:
            LOGGER.debug('Saving credentials...')
            os.makedirs(config.CONFIG_DIR, exist_ok=True)
            with open(CREDENTIALS_FILE, 'wb') as file:
                pickle.dump(credentials, file)

    return credentials
