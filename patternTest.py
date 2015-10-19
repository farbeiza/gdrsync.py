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

import pattern

import unittest

CHAR_CLASS_TEST = (pattern.CHAR_CLASS_START
                   + pattern.CHAR_CLASS_END
                   + "a"
                   + pattern.ESCAPE
                   + pattern.ASTERISK + pattern.ASTERISK
                   + pattern.QUESTION_MARK
                   + pattern.ESCAPE + pattern.CHAR_CLASS_END
                   + "b c"
                   + pattern.CHAR_CLASS_END)

TEXT_TEST = ("a"
             + pattern.ESCAPE
             + pattern.ESCAPE + pattern.ASTERISK
             + pattern.ESCAPE + pattern.QUESTION_MARK
             + pattern.ESCAPE + pattern.CHAR_CLASS_START
             + "b c")

MULTIPLE_TEST_CASES = {
    pattern.Token.MATCH_ALL: pattern.ASTERISK + pattern.ASTERISK,
    pattern.Token.MATCH_MULTIPLE: pattern.ASTERISK,
    pattern.Token.MATCH_ONE: pattern.QUESTION_MARK,
    pattern.Token.CHAR_CLASS: CHAR_CLASS_TEST,
    pattern.Token.MATCH_ALL: pattern.ASTERISK + pattern.ASTERISK
}

class LexerTestCase(unittest.TestCase):
    def testMatchAll(self):
        string = pattern.ASTERISK + pattern.ASTERISK
        self._testSingle(string, pattern.Token.MATCH_ALL)

    def _testSingle(self, string, tokenType):
        lexer = pattern.Lexer(string)

        token = lexer.token()
        self.assertEqual(token.type, tokenType)
        self.assertEqual(token.content, string)

        token = lexer.token()
        self.assertEqual(token, None)

    def testMatchMultiple(self):
        self._testSingle(pattern.ASTERISK, pattern.Token.MATCH_MULTIPLE)

    def testMatchOne(self):
        self._testSingle(pattern.QUESTION_MARK, pattern.Token.MATCH_ONE)

    def testCharClass(self):
        self._testSingle(CHAR_CLASS_TEST, pattern.Token.CHAR_CLASS)

    def testText(self):
        self._testSingle(TEXT_TEST, pattern.Token.TEXT)

    def testMultiple(self):
        string = TEXT_TEST
        for value in MULTIPLE_TEST_CASES.values():
            string += value
            string += TEXT_TEST

        lexer = pattern.Lexer(string)

        token = lexer.token()
        self.assertEqual(token.type, pattern.Token.TEXT)
        self.assertEqual(token.content, TEXT_TEST)

        for (type, value) in MULTIPLE_TEST_CASES.items():
            token = lexer.token()
            self.assertEqual(token.type, type)
            self.assertEqual(token.content, value)

            token = lexer.token()
            self.assertEqual(token.type, pattern.Token.TEXT)
            self.assertEqual(token.content, TEXT_TEST)

        token = lexer.token()
        self.assertEqual(token, None)

if __name__ == '__main__':
    unittest.main()
