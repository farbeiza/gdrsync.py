# gdrsync.py

Simple rsync utility for Google Drive.

## Prerequisites

### Python 3.3+

### Google APIs Client Library for Python

You can install it using pip:

    $ pip install --upgrade --requirement requirements.txt

More information [here](https://developers.google.com/docs/api/quickstart/python#step_2_install_the_google_client_library)

## Installation

You can just copy the directory anywhere and start using it:

    $ gdrsync.py -h

You may need to change the first line of gdrsync.py to point to your python
executable. For instance, if you are using Arch linux, you should change that
line to:

    #!/usr/bin/python3

## Configuration

Gdrsync.py will read some configuration options from the file `.config/gdrsync/config.ini` in
the user's home directory, if it exists.

    [gdrsync]
    clientId = xxxxxxxx
    clientSecret = xxxxxxxx

### clientId, clientSecret

Client information for API access.

Google places limits on API requests. Therefore, if you are going to make an
intensive use of gdrsync.py you should create your own access information to
prevent reaching those limits using the shared default access information.

To do so, sign up into
[Google API console](http://code.google.com/apis/console), and create a new
`Client ID for installed applications` in the `API access` section.
