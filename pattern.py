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

class Lexer(object):
    def __init__(self, string):
        self._string = string
        self._tokenContent = ""
        self._tokenIndex = 0

    def token(self):
        char = self.peek()
        if self.match(char, None):
            return None
        if self.match(char, ASTERISK):
            return self.handleAsterisk()
        if self.match(char, QUESTION_MARK):
            return self.handleQuestionMark()
        if self.match(char, CHAR_CLASS_START):
            return self.handleCharClass()

        return self.handleText()

    def handleAsterisk(self):
        self.read()
        if self.match(self.peek(), ASTERISK):
            self.read()

            return self._token(Token.MATCH_ALL)

        return self._token(Token.MATCH_MULTIPLE)

    def handleQuestionMark(self):
        self.read()

        return self._token(Token.MATCH_ONE)

    def handleCharClass(self):
        self.read(2)

        char = self.peek()
        while not self.match(char, None):
            self.read()
            if self.match(char, CHAR_CLASS_END):
                break
            if self.match(char, ESCAPE):
                if self.match(self.peek(), CHAR_CLASS_END):
                    self.read()

            char = self.peek()

        return self._token(Token.CHAR_CLASS)

    def handleText(self):
        char = self.peek()
        while not self.match(char, None):
            if self.match(char, WILDCARD_START):
                break

            self.read()
            if self.match(char, ESCAPE):
                if self.match(self.peek(), WILDCARD_START):
                    self.read()

            char = self.peek()

        return self._token(Token.TEXT)

    def match(self, left, right):
        if right is None:
            return left is None
        if left is None:
            return right is None

        return left in right

    def peek(self, offset = 0):
        if self._tokenIndex >= len(self._string):
            return None

        return self._string[self._tokenIndex]
    def read(self, length = 1):

        start = self._tokenIndex
        end = start + length
        if end > len(self._string):
            end = len(self._string)
        if end <= start:
            return None

        content = self._string[start:end]
        self._tokenContent += content
        self._tokenIndex += length

        return content

    def _token(self, type):
        tokenContent = self._tokenContent
        self._tokenContent = ""

        return Token(type, tokenContent)
