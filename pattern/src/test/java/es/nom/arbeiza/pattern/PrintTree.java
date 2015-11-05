package es.nom.arbeiza.pattern;

import com.google.common.collect.ImmutableList;
import org.antlr.v4.gui.TestRig;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.Collection;

public class PrintTree {
    public static void main(String... mainArgs) throws Exception {
        PrintTree printTree = new PrintTree();
        printTree.run();
    }

    private void run() throws Exception {
        this.print("/a-***?-b-[]a\\]/*?a]-c-[\\]-d-\\*\\?\\[/");
    }

    private void print(String string) throws Exception {
        ByteArrayInputStream in = new ByteArrayInputStream(string.getBytes(StandardCharsets.UTF_8));
        System.setIn(in);

        Collection<String> args = ImmutableList.<String>builder()
                .add("es.nom.arbeiza.pattern.Pattern").add("pattern")
                .add("-tree").add("-gui")
                .build();

        TestRig.main(args.stream().toArray(String[]::new));
    }
}
