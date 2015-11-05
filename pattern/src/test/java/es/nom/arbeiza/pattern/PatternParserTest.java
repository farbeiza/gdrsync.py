package es.nom.arbeiza.pattern;

import com.google.common.collect.ImmutableList;
import org.antlr.v4.runtime.ANTLRInputStream;
import org.antlr.v4.runtime.CommonTokenStream;
import org.antlr.v4.runtime.RuleContext;
import org.antlr.v4.runtime.TokenStream;
import org.antlr.v4.runtime.tree.ParseTreeWalker;
import org.mockito.Mockito;
import org.testng.Assert;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.util.Collection;
import java.util.function.Consumer;

@Test
public class PatternParserTest {
    private static final String TEXT_TEST = "a_b-c#d@";

    private static final Collection<String> CHAR_CLASS_TESTS = ImmutableList.<String>builder()
            .add(TestUtils.charClass(
                    TestUtils.TEST_CASES.get(PatternLexer.CHAR_CLASS_END)
                            + "a"
                            + TestUtils.TEST_CASES.get(PatternLexer.SLASH)
                            + TestUtils.escape()
                            + "b"
                            + TestUtils.TEST_CASES.get(PatternLexer.ASTERISK)
                            + TestUtils.TEST_CASES.get(PatternLexer.ASTERISK)
                            + TestUtils.TEST_CASES.get(PatternLexer.QUESTION_MARK)
                            + TestUtils.TEST_CASES.get(PatternLexer.CHAR_CLASS_START)
                            + TestUtils.escape(TestUtils.TEST_CASES.get(PatternLexer.CHAR_CLASS_END))
                            + "c"
            ))
            .add(TestUtils.charClass(TestUtils.escape()))
            .build();

    public void textTest() {
        this.test(TEXT_TEST, stub -> stub.enterText(Mockito.any()), stub -> stub.exitText(Mockito.any()));
    }

    public void slashTest() {
        this.test(TestUtils.TEST_CASES.get(PatternLexer.SLASH),
                stub -> stub.enterHeadingSlash(Mockito.any()),
                stub -> stub.exitHeadingSlash(Mockito.any()));
    }

    public void matchAllTest() {
        this.test(TestUtils.TEST_CASES.get(PatternLexer.ASTERISK) + TestUtils.TEST_CASES.get(PatternLexer.ASTERISK),
                stub -> stub.enterMatchAll(Mockito.any()),
                stub -> stub.exitMatchAll(Mockito.any()));
    }

    public void matchMultipleTest() {
        this.test(TestUtils.TEST_CASES.get(PatternLexer.ASTERISK),
                stub -> stub.enterMatchMultiple(Mockito.any()),
                stub -> stub.exitMatchMultiple(Mockito.any()));
    }

    public void matchOneTest() {
        this.test(TestUtils.TEST_CASES.get(PatternLexer.QUESTION_MARK),
                stub -> stub.enterMatchOne(Mockito.any()),
                stub -> stub.exitMatchOne(Mockito.any()));
    }

    public void escapeTest() {
        this.test(TestUtils.escape(),
                stub -> stub.enterSimpleEscape(Mockito.any()),
                stub -> stub.exitSimpleEscape(Mockito.any()));
    }

    public void escapedAsteriskTest() {
        this.test(TestUtils.escape(TestUtils.TEST_CASES.get(PatternLexer.ASTERISK)),
                stub -> stub.enterEscapedAsterisk(Mockito.any()),
                stub -> stub.exitEscapedAsterisk(Mockito.any()));
    }

    public void escapedQuestionMarkTest() {
        this.test(TestUtils.escape(TestUtils.TEST_CASES.get(PatternLexer.QUESTION_MARK)),
                stub -> stub.enterEscapedQuestionMark(Mockito.any()),
                stub -> stub.exitEscapedQuestionMark(Mockito.any()));
    }

    public void escapedCharClassStartTest() {
        this.test(TestUtils.escape(TestUtils.TEST_CASES.get(PatternLexer.CHAR_CLASS_START)),
                stub -> stub.enterEscapedCharClassStart(Mockito.any()),
                stub -> stub.exitEscapedCharClassStart(Mockito.any()));
    }

    @DataProvider(name = "charClassProvider")
    public Object[][] charClassProvider() {
        return CHAR_CLASS_TESTS.stream()
                .map(element -> new Object[]{element})
                .toArray(Object[][]::new);
    }

    @Test(dataProvider = "charClassProvider")
    public void charClassTest(String string) {
        this.test(string,
                stub -> stub.enterCharClass(Mockito.any()),
                stub -> stub.exitCharClass(Mockito.any()));
    }

    private void test(String string, Consumer<PatternListener>... verifications) {
        PatternLexer lexer = new PatternLexer(new ANTLRInputStream(string));
        TokenStream stream = new CommonTokenStream(lexer);
        PatternParser parser = new PatternParser(stream);

        ParseTreeWalker walker = new ParseTreeWalker();

        PatternListener listener = Mockito.mock(PatternListener.class);
        for (Consumer<PatternListener> verification : verifications) {
            PatternListener stub = Mockito.doAnswer(invocation -> {
                RuleContext context = invocation.getArgumentAt(0, RuleContext.class);
                Assert.assertEquals(context.getText(), string);

                return null;
            }).when(listener);

            verification.accept(stub);
        }

        PatternParser.PatternContext pattern = parser.pattern();
        walker.walk(listener, pattern);

        for (Consumer<PatternListener> verification : verifications) {
            verification.accept(Mockito.verify(listener));
        }
    }
}
