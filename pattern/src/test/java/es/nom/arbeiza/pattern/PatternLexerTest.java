package es.nom.arbeiza.pattern;

import org.antlr.v4.runtime.ANTLRInputStream;
import org.antlr.v4.runtime.Token;
import org.testng.Assert;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.util.Map;
import java.util.stream.Stream;

@Test
public class PatternLexerTest {
    @DataProvider(name = "dataProvider")
    public Object[][] dataProvider() {
        return TestUtils.TEST_CASES.entrySet().stream()
                .map(entry -> Stream.of(entry.getValue(), entry.getKey()).toArray(Object[]::new))
                .toArray(Object[][]::new);
    }

    @Test(dataProvider = "dataProvider")
    public void test(String string, int tokenType) {
        PatternLexer lexer = this.lexer(string);

        Token token;

        token = lexer.nextToken();
        Assert.assertEquals(token.getType(), tokenType);
        Assert.assertEquals(token.getText(), string);

        token = lexer.nextToken();
        Assert.assertEquals(token.getType(), PatternLexer.EOF);
    }

    private PatternLexer lexer(String string) {
        return new PatternLexer(new ANTLRInputStream(string));
    }

    public void testMultiple() {
        StringBuilder string = new StringBuilder();
        string.append(TestUtils.TEST_CASES.get(PatternLexer.ANY));
        for (String value : TestUtils.TEST_CASES.values()) {
            string.append(this.tokenString(value));
        }

        PatternLexer lexer = this.lexer(string.toString());

        Token token;

        token = lexer.nextToken();
        Assert.assertEquals(token.getType(), PatternLexer.ANY);
        Assert.assertEquals(token.getText(), TestUtils.TEST_CASES.get(PatternLexer.ANY));

        for (Map.Entry<Integer, String> entry : TestUtils.TEST_CASES.entrySet()) {
            this.assertToken(lexer, entry.getValue(), entry.getKey());
        }

        token = lexer.nextToken();
        Assert.assertEquals(token.getType(), PatternLexer.EOF);
    }

    private String tokenString(String value) {
        return value + TestUtils.TEST_CASES.get(PatternLexer.ANY);
    }

    private void assertToken(PatternLexer lexer, String value, int tokenType) {
        Token token;

        token = lexer.nextToken();
        Assert.assertEquals(token.getType(), tokenType);
        Assert.assertEquals(token.getText(), value);

        token = lexer.nextToken();
        Assert.assertEquals(token.getType(), PatternLexer.ANY);
        Assert.assertEquals(token.getText(), TestUtils.TEST_CASES.get(PatternLexer.ANY));
    }
}
