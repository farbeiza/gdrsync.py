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

EXCLUDE, INCLUDE = range(2)


def isExcluded(filters, file):
    if filters is None:
        return False

    for filter in filters:
        result = filter.check(file)
        if result == EXCLUDE:
            return True
        if result == INCLUDE:
            return False

    return False


class Filter(object):
    def __init__(self, regex, folder=None):
        self._regex = regex
        self._folder = folder

    def check(self, file):
        if self._check(file):
            return self._checkValue()

        return None

    def _check(self, file):
        if self._folder is not None:
            if file.folder != self._folder:
                return False

        return self._regex.match(file.location.relativePath)

    def _checkValue(self):
        raise NotImplementedError()


class Exclude(Filter):
    def __init__(self, regex, folder=None):
        super().__init__(regex, folder)

    def _checkValue(self):
        return EXCLUDE


class Include(Filter):
    def __init__(self, regex, folder=None):
        super().__init__(regex, folder)

    def _checkValue(self):
        return INCLUDE
