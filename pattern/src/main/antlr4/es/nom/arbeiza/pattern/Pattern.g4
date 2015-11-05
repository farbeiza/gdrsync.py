grammar Pattern;

pattern: headingSlash? patternContent trailingSlash?;

headingSlash: SLASH;
patternContent: (patternContentSlash | escapedPatternContent | wildcard | text)*?;
trailingSlash: SLASH;

patternContentSlash: SLASH;
escapedPatternContent: escapedWildcardStart | simpleEscape;
wildcard: exampleWildcard | charClass;
text: ANY+;

escapedWildcardStart: escapedAsterisk | escapedQuestionMark | escapedCharClassStart;
simpleEscape: ESCAPE;
exampleWildcard: matchAll | matchMultiple | matchOne;
charClass: CHAR_CLASS_START charClassFirst charClassRest CHAR_CLASS_END;

escapedAsterisk: ESCAPE ASTERISK;
escapedQuestionMark: ESCAPE QUESTION_MARK;
escapedCharClassStart: ESCAPE CHAR_CLASS_START;

matchAll: ASTERISK ASTERISK;
matchMultiple: ASTERISK;
matchOne: QUESTION_MARK;

charClassFirst: ESCAPE | CHAR_CLASS_END | charClassAny ;
charClassRest: (ESCAPE | escapedCharClassEnd | charClassAny)*;

charClassAny: SLASH | CHAR_CLASS_START | exampleWildcard | ANY;
escapedCharClassEnd: ESCAPE CHAR_CLASS_END;

SLASH: '/';
ESCAPE: '\\';
ASTERISK: '*';
QUESTION_MARK: '?';

CHAR_CLASS_START: '[';
CHAR_CLASS_END: ']';

ANY: .;
