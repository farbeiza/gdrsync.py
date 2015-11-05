package es.nom.arbeiza.pattern;

import com.google.common.collect.ImmutableMap;

import java.util.Map;

public class TestUtils {
    public static final Map<Integer, String> TEST_CASES = ImmutableMap.<Integer, String>builder()
            .put(PatternLexer.SLASH, "/")
            .put(PatternLexer.ESCAPE, "\\")
            .put(PatternLexer.ASTERISK, "*")
            .put(PatternLexer.QUESTION_MARK, "?")
            .put(PatternLexer.CHAR_CLASS_START, "[")
            .put(PatternLexer.CHAR_CLASS_END, "]")
            .put(PatternLexer.ANY, "a")
            .build();

    public static final String charClass(String string) {
        return TEST_CASES.get(PatternLexer.CHAR_CLASS_START)
                + string
                + TEST_CASES.get(PatternLexer.CHAR_CLASS_END);
    }

    public static final String escape() {
        return escape("");
    }

    public static final String escape(String string) {
        return TEST_CASES.get(PatternLexer.ESCAPE) + string;
    }
}
