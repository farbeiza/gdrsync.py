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
                   + pattern.SLASH
                   + pattern.ESCAPE
                   + pattern.ASTERISK + pattern.ASTERISK
                   + pattern.QUESTION_MARK
                   + pattern.ESCAPE + pattern.CHAR_CLASS_END
                   + "b c"
                   + pattern.CHAR_CLASS_END)

TEXT_TEST = "a_b-c#d@"

MULTIPLE_TEST_CASES = {
    pattern.Token.SLASH: pattern.SLASH,
    pattern.Token.MATCH_ALL: pattern.ASTERISK + pattern.ASTERISK,
    pattern.Token.MATCH_MULTIPLE: pattern.ASTERISK,
    pattern.Token.MATCH_ONE: pattern.QUESTION_MARK,
    pattern.Token.CHAR_CLASS: CHAR_CLASS_TEST,
    pattern.Token.ESCAPE: pattern.ESCAPE,
    pattern.Token.ESCAPED_ASTERISK: pattern.ESCAPE + pattern.ASTERISK,
    pattern.Token.ESCAPED_QUESTION_MARK: pattern.ESCAPE + pattern.QUESTION_MARK,
    pattern.Token.ESCAPED_CHAR_CLASS_START: pattern.ESCAPE + pattern.CHAR_CLASS_START
}

ESCAPED_TEST_CASES = [pattern.ASTERISK,
                      pattern.QUESTION_MARK,
                      pattern.CHAR_CLASS_START]

class LexerTestCase(unittest.TestCase):
    def testText(self):
        self._testSingle(TEXT_TEST, pattern.Token.TEXT)

    def _testSingle(self, string, tokenType):
        lexer = pattern.Lexer(string)

        token = next(lexer)
        self.assertEqual(token.type, tokenType)
        self.assertEqual(token.content, string)

        token = next(lexer)
        self.assertEqual(token, None)

    def testSlash(self):
        self._testSingle(pattern.SLASH, pattern.Token.SLASH)

    def testMatchAll(self):
        string = pattern.ASTERISK + pattern.ASTERISK
        self._testSingle(string, pattern.Token.MATCH_ALL)

    def testMatchMultiple(self):
        self._testSingle(pattern.ASTERISK, pattern.Token.MATCH_MULTIPLE)

    def testMatchOne(self):
        self._testSingle(pattern.QUESTION_MARK, pattern.Token.MATCH_ONE)

    def testCharClass(self):
        self._testSingle(CHAR_CLASS_TEST, pattern.Token.CHAR_CLASS)

    def testEscape(self):
        self._testSingle(pattern.ESCAPE, pattern.Token.ESCAPE)

    def testEscapedAsterisk(self):
        self._testSingle(pattern.ESCAPE + pattern.ASTERISK, pattern.Token.ESCAPED_ASTERISK)

    def testEscapedQuestionMark(self):
        self._testSingle(pattern.ESCAPE + pattern.QUESTION_MARK, pattern.Token.ESCAPED_QUESTION_MARK)

    def testEscapedCharClassStart(self):
        self._testSingle(pattern.ESCAPE + pattern.CHAR_CLASS_START,
                         pattern.Token.ESCAPED_CHAR_CLASS_START)

    def testMultiple(self):
        string = TEXT_TEST
        for value in MULTIPLE_TEST_CASES.values():
            string += value
            string += TEXT_TEST

        lexer = pattern.Lexer(string)

        token = next(lexer)
        self.assertEqual(token.type, pattern.Token.TEXT)
        self.assertEqual(token.content, TEXT_TEST)

        for (type, value) in MULTIPLE_TEST_CASES.items():
            token = next(lexer)
            self.assertEqual(token.type, type)
            self.assertEqual(token.content, value)

            token = next(lexer)
            self.assertEqual(token.type, pattern.Token.TEXT)
            self.assertEqual(token.content, TEXT_TEST)

        token = next(lexer)
        self.assertEqual(token, None)

class ParserTestCase(unittest.TestCase):
    def testText(self):
        self._test(TEXT_TEST,
                   match = [TEXT_TEST],
                   notMatch = [])

    def testEscape(self):
        escaped = pattern.ESCAPE + pattern.ESCAPE.join(ESCAPED_TEST_CASES) + pattern.ESCAPE
        notEscaped = "".join(ESCAPED_TEST_CASES) + pattern.ESCAPE

        self._test(escaped,
                   match = [notEscaped],
                   notMatch = [escaped])

    def testLeadingSlash(self):
        self._test(pattern.SLASH + "foo",
                   match = ["foo", "foo/bar"],
                   notMatch = ["bar/foo"])

    def testMatchAll(self):
        self._test(pattern.ASTERISK + pattern.ASTERISK,
                   match = ["foo", "foo/bar"],
                   notMatch = [])

        self._test("foo" + pattern.ASTERISK + pattern.ASTERISK + "bar",
                   match = ["foobar", "foo/bar", "foobazbar", "foo/baz/bar"],
                   notMatch = [])

        self._test("foo/" + pattern.ASTERISK + pattern.ASTERISK + "/bar",
                   match = ["foo//bar", "foo/baz/bar", "foo/baz/qux/bar"],
                   notMatch = [])

    def testMatchMultiple(self):
        self._test(pattern.ASTERISK,
                   match = ["foo", "foo/bar"],
                   notMatch = [])

        self._test("foo" + pattern.ASTERISK + "bar",
                   match = ["foobar", "foobazbar"],
                   notMatch = ["foo/bar", "foo/baz/bar"])

        self._test("foo/" + pattern.ASTERISK + "/bar",
                   match = ["foo//bar", "foo/baz/bar"],
                   notMatch = ["foo/baz/qux/bar"])

    def testMatchOne(self):
        self._test(pattern.QUESTION_MARK,
                   match = ["foo", "foo/bar"],
                   notMatch = [])

        self._test("foo" + pattern.QUESTION_MARK + "bar",
                   match = ["foo_bar"],
                   notMatch = ["foobar", "foo/bar"])

        self._test("foo/" + pattern.QUESTION_MARK + "/bar",
                   match = ["foo/b/bar"],
                   notMatch = ["foo//bar", "foo///bar", "foo/baz/bar", "foo/baz/qux/bar"])

    def testCharClass(self):
        self._test(self._charClass("fo") + self._charClass("fo") + self._charClass("fo"),
                   match = ["foo"],
                   notMatch = ["foo/bar"])

        self._test("foo" + self._charClass("abz") + "bar",
                   match = ["foobbar", "fooabar", "foozbar"],
                   notMatch = ["foo/bar", "foo_bar"])

    def _charClass(self, string):
        return pattern.CHAR_CLASS_START + string + pattern.CHAR_CLASS_END

    def _test(self, patternString, match = [], notMatch = []):
        for string in match:
            self._testSingle(patternString, string, True)
        for string in notMatch:
            self._testSingle(patternString, string, False)

    def _testSingle(self, patternString, string, expected):
        lexer = pattern.Lexer(patternString)
        parser = pattern.Parser(lexer)
        regex = parser.regex

        actual = regex.match(string) is not None
        self.assertEqual(actual, expected,
                         "Pattern: /%s/, String: \"%s\"" % (patternString, string))

if __name__ == '__main__':
    unittest.main(verbosity = 2)
