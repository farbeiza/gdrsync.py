# gdrsync.py

Simple rsync utility for Google Drive (for uploading only).

## Prerequisites

### Python 2

Google API libraries do not support Python 3 yet.

### Google APIs Client Library for Python

You can install it using easy_install:

    $ easy_install --upgrade google-api-python-client

or pip:

    $ pip install --upgrade google-api-python-client

More information [here](https://developers.google.com/api-client-library/python/start/installation)

## Installation

You can just copy the directory anywhere and start using it:

    $ gdrsync.py -h

You may need to change the first line of gdrsync.py to point to your python 2
executable. For instance, if you are using Arch linux, you should change that
line to:

    #!/usr/bin/python2

## Configuration

Gdrsync.py will read some configuration options from the file `.gdrsync.py` in
the user's home directory, if it exists.

    [gdrsync]
    clientId = xxxxxxxx
    clientSecret = xxxxxxxx
    refreshToken = xxxxxxxx

### clientId, clientSecret

Client information for API access.

Google places limits on API requests. Therefore, if you are going to make an
intensive use of gdrsync.py you should create your own access information to
prevent reaching those limits using the shared default access information.

To do so, sign up into
[Google API console](http://code.google.com/apis/console), and create a new
`Client ID for installed applications` in the `API access` section.

### refreshToken

Token for user authentication.

Gdrsync.py will write this option if called using the command line argument
`-s`.
