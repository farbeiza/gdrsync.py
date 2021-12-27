#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Fernando Arbeiza <fernando.arbeiza@gmail.com>
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

import argparse
import os.path
import re

import filter
import pattern

PARSER = argparse.ArgumentParser(description='Copy files between a local system and a Google drive repository.',
                                 epilog='Source and destination URLs may be local or remote. '
                                        ' Local URLs: URLs with the form file:///path'
                                        ' or file://host/path or native path names.'
                                        ' Remote URLs: A URL with the form gdrive:///path,'
                                        ' gdrive://host/path or gdrive:/path.')

NATIVE_TRAILING_MESSAGE = ''
if os.path.sep != '/':
    NATIVE_TRAILING_MESSAGE = ' (or %s, if a local native path name)' % os.path.sep

PARSER.add_argument('sourceUrls', nargs='+',
                    help=('source URLs.'
                          ' A trailing /%s means "copy the contents of this directory",'
                          ' as opposed to "copy the directory itself".'
                          % NATIVE_TRAILING_MESSAGE),
                    metavar='SOURCE')
PARSER.add_argument('destUrl', help='destination URL. It must be a directory. It will be created if necessary',
                    metavar='DEST')

PARSER.add_argument('-c', '--checksum', action='store_true',
                    help='skip based on checksum, not mod-time & size')
PARSER.add_argument('-L', '--copy-links', action='store_true', dest='copyLinks',
                    help='transform symlink into referent file/dir')
PARSER.add_argument('--delete', action='store_true',
                    help='delete duplicate and extraneous files from dest dirs')
PARSER.add_argument('--delete-excluded', action='store_true', dest='deleteExcluded',
                    help='also delete excluded files from dest dirs')


class FilterAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")

        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        filters = getattr(namespace, self.dest, [])
        if filters is None:
            filters = []

        filter = self.filter(values)
        filters.append(filter)

        setattr(namespace, self.dest, filters)

    def filter(self, value):
        raise NotImplementedError()


class ExcludeAction(FilterAction):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def filter(self, value):
        return pattern.filter(value, filter.Exclude)


class IncludeAction(FilterAction):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def filter(self, value):
        return pattern.filter(value, filter.Include)


class RegexExcludeAction(FilterAction):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def filter(self, value):
        regex = re.compile(value)
        return filter.Exclude(regex)


class RegexIncludeAction(FilterAction):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def filter(self, value):
        regex = re.compile(value)
        return filter.Include(regex)


PARSER.add_argument('--exclude', action=ExcludeAction, dest='filters',
                    help='exclude files matching PATTERN', metavar='PATTERN')
PARSER.add_argument('--include', action=IncludeAction, dest='filters',
                    help='don\'t exclude files matching PATTERN', metavar='PATTERN')
PARSER.add_argument('--rexclude', action=RegexExcludeAction, dest='filters',
                    help='exclude files matching REGEX', metavar='REGEX')
PARSER.add_argument('--rinclude', action=RegexIncludeAction, dest='filters',
                    help='don\'t exclude files matching REGEX', metavar='REGEX')

PARSER.add_argument('-n', '--dry-run', action='store_true', dest='dryRun',
                    help='perform a trial run with no changes made')
PARSER.add_argument('-r', '--recursive', action='store_true',
                    help='recurse into directories')
PARSER.add_argument('-p', '--update-credentials', action='store_true', dest='updateCredentials',
                    help='update credentials')
PARSER.add_argument('-P', '--ignore-credentials', action='store_true', dest='ignoreCredentials',
                    help='ignore existing credentials')
PARSER.add_argument('-u', '--update', action='store_true',
                    help='skip files that are newer on the receiver')
PARSER.add_argument('-v', '--verbose', action='count', default=0, dest='verbosity',
                    help='increase verbosity')
