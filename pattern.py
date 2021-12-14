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

import collections
import itertools
import re

import exception

SLASH = "/"

ESCAPE = "\\"

ASTERISK = "*"
QUESTION_MARK = "?"

CHAR_CLASS_START = "["
CHAR_CLASS_END = "]"

NOT_TEXT = SLASH + ESCAPE + ASTERISK + QUESTION_MARK + CHAR_CLASS_START


def filter(pattern, filterClass):
    lexer = Lexer(pattern)
    parser = Parser(lexer)

    return parser.filter(filterClass)


class Token(object):
    (
        TEXT,
        SLASH,
        MATCH_ALL, MATCH_MULTIPLE, MATCH_ONE, CHAR_CLASS,
        ESCAPE,
        ESCAPED_ASTERISK, ESCAPED_QUESTION_MARK, ESCAPED_CHAR_CLASS_START
    ) = range(10)

    def __init__(self, type, content):
        self._type = type
        self._content = content

    @property
    def type(self):
        return self._type

    @property
    def content(self):
        return self._content


class PeekableDecorator(object):
    def __init__(self, delegate):
        self._delegate = iter(delegate)
        self._cache = collections.deque()

    def __iter__(self):
        return self

    def __next__(self):
        if not self._cache:
            return next(self._delegate)

        return self._cache.popleft()

    def next(self, size):
        self._fillcache(size)

        return self._popleft(size)

    def _fillcache(self, size):
        while len(self._cache) < size:
            try:
                self._cache.append(next(self._delegate))
            except StopIteration:
                break

    def _popleft(self, size):
        result = list(itertools.islice(self._cache, 0, size))
        for i in range(size):
            if not self._cache:
                break

            self._cache.popleft()

        return result

    def peek(self, offset=0):
        self._fillcache(offset + 1)

        if offset >= len(self._cache):
            return None

        return self._cache[offset]


class Lexer(object):
    def __init__(self, string):
        self._charBuffer = PeekableDecorator(string)
        self._tokenContent = ""

    def __iter__(self):
        return self

    def __next__(self):
        if self._expect(None):
            return None
        if self._accept(SLASH):
            return self._slash()
        if self._accept(ESCAPE):
            return self._escape()
        if self._accept(ASTERISK):
            return self._asterisk()
        if self._accept(QUESTION_MARK):
            return self._questionMark()
        if self._accept(CHAR_CLASS_START):
            return self._charClass()

        return self._text()

    def _slash(self):
        return self._token(Token.SLASH)

    def _escape(self):
        if self._accept(ASTERISK):
            return self._escapedAsterisk()
        if self._accept(QUESTION_MARK):
            return self._escapedQuestionMark()
        if self._accept(CHAR_CLASS_START):
            return self._escapedCharClassStart()

        return self._token(Token.ESCAPE)

    def _escapedAsterisk(self):
        return self._token(Token.ESCAPED_ASTERISK)

    def _escapedQuestionMark(self):
        return self._token(Token.ESCAPED_QUESTION_MARK)

    def _escapedCharClassStart(self):
        return self._token(Token.ESCAPED_CHAR_CLASS_START)

    def _asterisk(self):
        if self._accept(ASTERISK):
            return self._token(Token.MATCH_ALL)

        return self._token(Token.MATCH_MULTIPLE)

    def _questionMark(self):
        return self._token(Token.MATCH_ONE)

    def _charClass(self):
        self._read()

        while not self._expect(None):
            if self._accept(CHAR_CLASS_END):
                break
            if self._accept(ESCAPE):
                self._charClassEscape()
            else:
                self._read()

        return self._token(Token.CHAR_CLASS)

    def _charClassEscape(self):
        self._accept(CHAR_CLASS_END)

    def _text(self):
        while not self._expect(None):
            if self._expect(NOT_TEXT):
                break

            self._read()

        return self._token(Token.TEXT)

    def _expect(self, char, offset=0):
        return self._match(self._peek(offset), char)

    def _accept(self, char):
        if not self._expect(char):
            return False

        self._read()

        return True

    def _match(self, left, right):
        if right is None:
            return left is None
        if left is None:
            return right is None

        return left in right

    def _peek(self, offset=0):
        return self._charBuffer.peek(offset)

    def _read(self, maxLength=1):
        content = self._charBuffer.next(maxLength)
        if not content:
            return None

        content = "".join(content)

        self._tokenContent += content

        return content

    def _token(self, type):
        tokenContent = self._tokenContent
        self._tokenContent = ""

        return Token(type, tokenContent)


class Parser(object):
    def __init__(self, lexer):
        self._lexer = PeekableDecorator(lexer)

        self._regex = ""
        self._root = False
        self._folder = None

    def filter(self, filterClass):
        self._pattern()
        if not self._expect(None):
            raise exception.PatternException(f'Unexpected token: {self._read()}')

        if self._root:
            self._regex = "^" + self._regex
        else:
            self._regex = ".*" + self._regex + "$"

        regex = re.compile(self._regex)

        return filterClass(regex, self._folder)

    def _pattern(self):
        self._leadingSlash()
        self._patternContent()
        self._trailingSlash()

    def _leadingSlash(self):
        if self._expect(Token.SLASH):
            token = self._read()
            self._root = True

            return True

        return False

    def _patternContent(self):
        while (self._patternContentSlash()
               or self._escapedPatternContent()
               or self._wildcard()
               or self._text()):
            pass

        return True

    def _trailingSlash(self):
        if self._expect(Token.SLASH):
            token = self._read()
            self._folder = True

            return True

        return False

    def _patternContentSlash(self):
        if self._expect(Token.SLASH):
            token = self._read()

            if self._expect(Token.SLASH):
                return False

            self._regex += token.content

            return True

        return False

    def _escapedPatternContent(self):
        if self._escapedWildcardStart():
            return True
        if self._expect(Token.ESCAPE):
            token = self._read()
            self._regex += re.escape(token.content)

            return True

        return False

    def _wildcard(self):
        if self._matchAll():
            return True
        if self._matchMultiple():
            return True
        if self._matchOne():
            return True
        if self._charClass():
            return True

        return False

    def _text(self):
        if self._expect(Token.TEXT):
            token = self._read()
            self._regex += re.escape(token.content)

            return True

        return False

    def _escapedWildcardStart(self):
        if self._escapedAsterisk():
            return True
        if self._escapedQuestionMark():
            return True
        if self._escapedCharClassStart():
            return True

        return False

    def _escapedAsterisk(self):
        if self._expect(Token.ESCAPED_ASTERISK):
            token = self._read()
            self._regex += re.escape(ASTERISK)

            return True

        return False

    def _escapedQuestionMark(self):
        if self._expect(Token.ESCAPED_QUESTION_MARK):
            token = self._read()
            self._regex += re.escape(QUESTION_MARK)

            return True

        return False

    def _escapedCharClassStart(self):
        if self._expect(Token.ESCAPED_CHAR_CLASS_START):
            token = self._read()
            self._regex += re.escape(CHAR_CLASS_START)

            return True

        return False

    def _matchAll(self):
        if self._expect(Token.MATCH_ALL):
            token = self._read()
            self._regex += ".*"

            return True

        return False

    def _matchMultiple(self):
        if self._expect(Token.MATCH_MULTIPLE):
            token = self._read()
            self._regex += "[^/]*"

            return True

        return False

    def _matchOne(self):
        if self._expect(Token.MATCH_ONE):
            token = self._read()
            self._regex += "[^/]"

            return True

        return False

    def _charClass(self):
        if self._expect(Token.CHAR_CLASS):
            token = self._read()
            self._regex += token.content

            return True

        return False

    def _expect(self, tokenType, offset=0):
        return self._match(self._lexer.peek(offset), tokenType)

    def _match(self, token, tokenType):
        if token is None:
            return tokenType is None

        return token.type == tokenType

    def _read(self):
        return next(self._lexer, None)
