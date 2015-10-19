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

ESCAPE = "\\"

ASTERISK = "*"
QUESTION_MARK = "?"

CHAR_CLASS_START = "["
CHAR_CLASS_END = "]"

WILDCARD_START = ASTERISK + QUESTION_MARK + CHAR_CLASS_START

class Token(object):
    TEXT, MATCH_ALL, MATCH_MULTIPLE, MATCH_ONE, CHAR_CLASS = range(5)

    def __init__(self, type, content):
        self._type = type
        self._content = content

    @property
    def type(self):
        return self._type

    @property
    def content(self):
        return self._content

class StringBuffer(object):
    def __init__(self, string):
        self._string = string
        self._index = 0

    def peek(self, offset = 0):
        if self._index >= len(self._string):
            return None

        return self._string[self._index]

    def read(self, maxLength = 1):
        start = self._index
        end = start + maxLength
        if end > len(self._string):
            end = len(self._string)
        if end <= start:
            return None

        self._index = end

        return self._string[start:end]

class Lexer(object):
    def __init__(self, stringBuffer):
        self._stringBuffer = stringBuffer
        self._tokenContent = ""

    def token(self):
        char = self._peek()
        if self._match(char, None):
            return None
        if self._match(char, ASTERISK):
            return self._handleAsterisk()
        if self._match(char, QUESTION_MARK):
            return self._handleQuestionMark()
        if self._match(char, CHAR_CLASS_START):
            return self._handleCharClass()

        return self._handleText()

    def _handleAsterisk(self):
        self._read()
        if self._match(self._peek(), ASTERISK):
            self._read()

            return self._token(Token.MATCH_ALL)

        return self._token(Token.MATCH_MULTIPLE)

    def _handleQuestionMark(self):
        self._read()

        return self._token(Token.MATCH_ONE)

    def _handleCharClass(self):
        self._read(2)

        char = self._peek()
        while not self._match(char, None):
            self._read()
            if self._match(char, CHAR_CLASS_END):
                break
            if self._match(char, ESCAPE):
                if self._match(self._peek(), CHAR_CLASS_END):
                    self._read()

            char = self._peek()

        return self._token(Token.CHAR_CLASS)

    def _handleText(self):
        char = self._peek()
        while not self._match(char, None):
            if self._match(char, WILDCARD_START):
                break

            self._read()
            if self._match(char, ESCAPE):
                if self._match(self._peek(), WILDCARD_START):
                    self._read()

            char = self._peek()

        return self._token(Token.TEXT)

    def _peek(self, offset = 0):
        return self._stringBuffer.peek(offset)

    def _read(self, maxLength = 1):
        content = self._stringBuffer.read(maxLength)
        if content is None:
            return None

        self._tokenContent += content

        return content

    def _match(self, left, right):
        if right is None:
            return left is None
        if left is None:
            return right is None

        return left in right

    def _token(self, type):
        tokenContent = self._tokenContent
        self._tokenContent = ""

        return Token(type, tokenContent)
