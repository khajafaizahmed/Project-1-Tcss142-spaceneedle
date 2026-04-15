import java.io.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Project1LocalTester {

    /* ================== CONFIG ================== */

    // Set to true to print every compared line.
    private static final boolean DEBUG = false;

    // Number of surrounding lines shown near the first mismatch.
    private static final int CONTEXT = 2;

    // Safety timeouts.
    private static final long COMPILE_TIMEOUT_SECONDS = 20;
    private static final long RUN_TIMEOUT_SECONDS = 20;

    private static final String STUDENT_FILE = "Project1.java";
    private static final String STUDENT_CLASS = "Project1";
    private static final String REFERENCE_FILE = "SpaceNeedle.txt";

    /* ================== MAIN ================== */

    public static void main(String[] args) throws Exception {
        System.out.println("=== TCSS 142 · Project 1 TA Tester ===\n");

        forceCompile();

        int size = detectSize();
        if (size == -1) {
            System.out.println("❌ Could not detect the SIZE constant in " + STUDENT_FILE);
            System.out.println("Make sure the file contains a line like:");
            System.out.println("public static final int SIZE = 3;");
            return;
        }

        List<String> expected = loadReference(size);
        if (expected.isEmpty()) {
            System.out.println("❌ No reference output found for SIZE = " + size);
            System.out.println("Check that " + REFERENCE_FILE + " contains a block beginning with:");
            System.out.println("SIZE = " + size);
            return;
        }

        RunResult run = runStudent();
        if (run.timedOut) {
            reportTimeout(run.lines);
            return;
        }

        if (run.exitCode != 0) {
            reportRuntimeError(run);
            return;
        }

        List<String> actual = run.lines;
        int firstDiff = firstDifference(expected, actual);

        if (firstDiff == -1) {
            System.out.println("✅ PASS (SIZE = " + size + ")");
            System.out.println("Your output matches the reference output.");
            return;
        }

        if (expected.size() != actual.size()) {
            reportLineCount(size, expected, actual, firstDiff);
        } else {
            reportMismatch(size, expected, actual, firstDiff);
        }
    }

    /* ================== DATA TYPES ================== */

    private static class RunResult {
        private final List<String> lines;
        private final int exitCode;
        private final boolean timedOut;

        private RunResult(List<String> lines, int exitCode, boolean timedOut) {
            this.lines = lines;
            this.exitCode = exitCode;
            this.timedOut = timedOut;
        }
    }

    private static class StreamCollector extends Thread {
        private final InputStream in;
        private final List<String> lines;
        private Exception error;

        private StreamCollector(InputStream in) {
            this.in = in;
            this.lines = Collections.synchronizedList(new ArrayList<>());
            setDaemon(true);
        }

        @Override
        public void run() {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(in))) {
                String line;
                while ((line = br.readLine()) != null) {
                    lines.add(line);
                }
            } catch (Exception e) {
                error = e;
            }
        }

        private List<String> getLines() {
            synchronized (lines) {
                return new ArrayList<>(lines);
            }
        }

        private void rethrowIfNeeded() throws Exception {
            if (error != null) {
                throw error;
            }
        }
    }

    /* ================== EXECUTION ================== */

    private static void forceCompile() throws Exception {
        Process compile = startProcess(
                new ProcessBuilder("javac", STUDENT_FILE).redirectErrorStream(true),
                "compiler",
                "Make sure Java is installed and that javac is on your PATH."
        );

        StreamCollector collector = new StreamCollector(compile.getInputStream());
        collector.start();

        boolean finished = compile.waitFor(COMPILE_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        if (!finished) {
            compile.destroyForcibly();
            compile.waitFor(2, TimeUnit.SECONDS);
            collector.join(2000);

            List<String> messages = collector.getLines();

            System.out.println("❌ COMPILATION TIMED OUT");
            System.out.println("The file took too long to compile.");
            System.out.println("This can happen if javac is misconfigured or if the tester is run from a slow/cloud-synced folder.");

            if (!messages.isEmpty()) {
                System.out.println("\nCompiler output captured before timeout:");
                for (String line : messages) {
                    System.out.println(line);
                }
            }

            System.exit(1);
        }

        collector.join(2000);
        collector.rethrowIfNeeded();
        List<String> messages = collector.getLines();

        if (compile.exitValue() != 0) {
            System.out.println("❌ COMPILATION FAILED");
            if (messages.isEmpty()) {
                System.out.println("javac reported an error, but no compiler output was captured.");
            } else {
                for (String line : messages) {
                    System.out.println(line);
                }
            }
            System.exit(1);
        }
    }

    private static RunResult runStudent() throws Exception {
        Process p = startProcess(
                new ProcessBuilder("java", STUDENT_CLASS).redirectErrorStream(true),
                "program",
                "Make sure Java is installed and that the compiled class can be run with 'java " + STUDENT_CLASS + "'."
        );

        StreamCollector collector = new StreamCollector(p.getInputStream());
        collector.start();

        boolean finished = p.waitFor(RUN_TIMEOUT_SECONDS, TimeUnit.SECONDS);
        if (!finished) {
            p.destroyForcibly();
            p.waitFor(2, TimeUnit.SECONDS);
            collector.join(2000);
            return new RunResult(cleanLines(collector.getLines()), -1, true);
        }

        collector.join(2000);
        collector.rethrowIfNeeded();
        return new RunResult(cleanLines(collector.getLines()), p.exitValue(), false);
    }

    private static Process startProcess(ProcessBuilder builder,
                                        String label,
                                        String helpMessage) throws Exception {
        try {
            return builder.start();
        } catch (IOException e) {
            System.out.println("❌ COULD NOT START " + label.toUpperCase());
            System.out.println(helpMessage);
            System.out.println("Details: " + e.getMessage());
            System.exit(1);
            return null;
        }
    }

    private static List<String> cleanLines(List<String> lines) {
        List<String> cleaned = new ArrayList<>();
        for (String line : lines) {
            cleaned.add(rstrip(line));
        }
        return cleaned;
    }

    private static int detectSize() throws Exception {
        Pattern pattern = Pattern.compile("\\bSIZE\\s*=\\s*(\\d+)\\s*;");

        try (Scanner sc = new Scanner(new File(STUDENT_FILE))) {
            while (sc.hasNextLine()) {
                String line = sc.nextLine();
                Matcher m = pattern.matcher(line);
                if (m.find()) {
                    return Integer.parseInt(m.group(1));
                }
            }
        }

        return -1;
    }

    /* ================== REFERENCE LOADING ================== */

    private static List<String> loadReference(int size) throws Exception {
        List<String> ref = new ArrayList<>();
        boolean active = false;

        File f = new File(REFERENCE_FILE);
        if (!f.exists()) {
            System.out.println("❌ Missing " + REFERENCE_FILE);
            System.out.println("Place " + REFERENCE_FILE + " in the same folder as this tester.");
            System.exit(1);
        }

        try (Scanner sc = new Scanner(f)) {
            while (sc.hasNextLine()) {
                String line = sc.nextLine();

                if (line.trim().equals("SIZE = " + size)) {
                    active = true;
                    continue;
                }

                if (active && line.trim().startsWith("SIZE =")) {
                    break;
                }

                if (active) {
                    String trimmed = rstrip(line);

                    // Ignore blank separator lines in the reference file.
                    if (!trimmed.isEmpty()) {
                        ref.add(trimmed);
                    }
                }
            }
        }

        return ref;
    }

    /* ================== COMPARISON ================== */

    private static int firstDifference(List<String> expected, List<String> actual) {
        int limit = Math.min(expected.size(), actual.size());

        for (int i = 0; i < limit; i++) {
            if (DEBUG) {
                System.out.printf(
                        "[DEBUG] line %2d | expected=%s | yours=%s%n",
                        i + 1,
                        showSpaces(expected.get(i)),
                        showSpaces(actual.get(i))
                );
            }

            if (!expected.get(i).equals(actual.get(i))) {
                return i;
            }
        }

        if (expected.size() != actual.size()) {
            return limit;
        }

        return -1;
    }

    /**
     * Detects whether the mismatch is caused by one clean missing or extra block.
     *
     * Returns:
     *   positive number -> missing expected lines
     *   negative number -> extra actual lines
     *   zero            -> no clean one-block shift found
     */
    private static int detectSingleBlockShift(List<String> expected,
                                              List<String> actual,
                                              int firstDiff) {
        int delta = expected.size() - actual.size();

        if (delta > 0) {
            for (int i = firstDiff; i < actual.size(); i++) {
                if (!expected.get(i + delta).equals(actual.get(i))) {
                    return 0;
                }
            }
            return delta;
        } else if (delta < 0) {
            int extra = -delta;
            for (int i = firstDiff; i < expected.size(); i++) {
                if (!expected.get(i).equals(actual.get(i + extra))) {
                    return 0;
                }
            }
            return -extra;
        }

        return 0;
    }

    /* ================== ERROR REPORTING ================== */

    private static void reportTimeout(List<String> partialOutput) {
        System.out.println("❌ PROGRAM TIMED OUT");
        System.out.println("The program did not finish within " + RUN_TIMEOUT_SECONDS + " seconds.");
        System.out.println("Possible causes:");
        System.out.println("• An infinite loop");
        System.out.println("• A loop bound that never becomes false");
        System.out.println("• Waiting for keyboard input when this assignment should only print output");

        if (!partialOutput.isEmpty()) {
            System.out.println("\nProgram output captured before timeout:");
            for (String line : partialOutput) {
                System.out.println(line);
            }
        }
    }

    private static void reportRuntimeError(RunResult run) {
        System.out.println("❌ PROGRAM CRASHED");
        System.out.println("The program compiled, but it did not finish normally.");

        if (!run.lines.isEmpty()) {
            System.out.println("\nProgram output / error message:");
            for (String line : run.lines) {
                System.out.println(line);
            }
        }
    }

    private static void reportLineCount(int size,
                                        List<String> expected,
                                        List<String> actual,
                                        int firstDiff) {

        int diff = expected.size() - actual.size();

        System.out.println("❌ LINE COUNT MISMATCH (SIZE = " + size + ")");
        System.out.println("Expected total lines: " + expected.size());
        System.out.println("Your program printed: " + actual.size());

        if (diff > 0) {
            System.out.println("Difference: missing " + diff + " line(s)");
        } else {
            System.out.println("Difference: " + (-diff) + " extra line(s)");
        }

        int min = Math.min(expected.size(), actual.size());

        if (firstDiff == min) {
            System.out.println("\nAll lines matched through line " + firstDiff + ".");

            if (diff > 0) {
                System.out.println("Your output stops too early after that point.");
            } else {
                System.out.println("Your program prints extra line(s) after that point.");
            }
        } else {
            int line = firstDiff + 1;
            System.out.println("\nThe first place your output stops matching is line "
                    + line + " (" + sectionNameForLine(size, line) + ").");
        }

        System.out.println("\nSpaces are shown as · below so indentation problems are visible.");
        printContext(expected, actual, firstDiff);

        int shift = detectSingleBlockShift(expected, actual, firstDiff);

        if (shift > 0) {
            System.out.println("\nAfter skipping " + shift
                    + " expected line(s), the rest of the output matches again.");
            System.out.println("That usually means one whole section is missing.");
            printPreview("Missing expected line(s):", expected, firstDiff, shift);
        } else if (shift < 0) {
            int extra = -shift;
            System.out.println("\nAfter skipping " + extra
                    + " extra line(s) from your output, the rest matches again.");
            System.out.println("That usually means one whole section was printed an extra time.");
            printPreview("Extra line(s) your program printed:", actual, firstDiff, extra);
        }

        printHints(buildHints(size, expected, actual, firstDiff));
        printSectionSizeReminder(size);
    }

    private static void reportMismatch(int size,
                                       List<String> expected,
                                       List<String> actual,
                                       int firstDiff) {

        int line = firstDiff + 1;
        String exp = expected.get(firstDiff);
        String got = actual.get(firstDiff);

        System.out.println("❌ OUTPUT MISMATCH (SIZE = " + size + ")");
        System.out.println("First difference at line " + line
                + " (" + sectionNameForLine(size, line) + ").");

        System.out.println("\nExpected line:");
        System.out.println(showSpaces(exp));

        System.out.println("\nYour line:");
        System.out.println(showSpaces(got));

        System.out.println("\nSpaces are shown as · below so indentation problems are visible.");
        printContext(expected, actual, firstDiff);

        printHints(buildHints(size, expected, actual, firstDiff));
    }

    private static void printContext(List<String> expected,
                                     List<String> actual,
                                     int index) {
        int maxLines = Math.max(expected.size(), actual.size());
        int start = Math.max(0, index - CONTEXT);
        int end = Math.min(maxLines, index + CONTEXT + 3);

        for (int i = start; i < end; i++) {
            String exp = i < expected.size() ? showSpaces(expected.get(i)) : "<no line>";
            String act = i < actual.size() ? showSpaces(actual.get(i)) : "<no line>";
            String mark = (i == index ? ">>" : "  ");
            System.out.printf("%s line %2d | expected=%s | yours=%s%n",
                    mark, i + 1, exp, act);
        }
    }

    private static void printPreview(String title,
                                     List<String> lines,
                                     int start,
                                     int count) {
        System.out.println("\n" + title);

        int preview = Math.min(count, 6);
        for (int i = 0; i < preview; i++) {
            int lineIndex = start + i;
            if (lineIndex >= lines.size()) {
                break;
            }
            System.out.printf("   line %2d | %s%n",
                    lineIndex + 1,
                    showSpaces(lines.get(lineIndex)));
        }

        if (count > preview) {
            System.out.println("   ... and " + (count - preview) + " more line(s)");
        }
    }

    private static void printHints(List<String> hints) {
        System.out.println("\nHelpful hint(s):");
        for (String hint : hints) {
            System.out.println("• " + hint);
        }
    }

    private static List<String> buildHints(int size,
                                           List<String> expected,
                                           List<String> actual,
                                           int firstDiff) {
        List<String> hints = new ArrayList<>();

        int delta = expected.size() - actual.size();

        if (delta == size) {
            hints.add("You are short by SIZE lines. A repeated SIZE-line section may be missing.");
        }
        if (delta == 1) {
            hints.add("You are short by 1 line. Check whether one deck line is missing.");
        }
        if (delta == 4 * size) {
            hints.add("You are short by 4 × SIZE lines. Check the height of the tower section.");
        }
        if (delta == -size) {
            hints.add("You have SIZE extra lines. A repeated SIZE-line section may be printed twice.");
        }
        if (delta == -(4 * size)) {
            hints.add("You have 4 × SIZE extra lines. Check the height of the tower section.");
        }

        String expectedType = firstDiff < expected.size() ? lineType(expected.get(firstDiff)) : "no line";
        String actualType = firstDiff < actual.size() ? lineType(actual.get(firstDiff)) : "no line";

        if ("spire".equals(expectedType) && "roof/base".equals(actualType)) {
            hints.add("Your output seems to jump straight into the roof/base. The figure should begin with the upper spire.");
        }

        if ("deck".equals(expectedType) && !"deck".equals(actualType)) {
            hints.add("A deck line is expected here. Check whether the deck section is missing or printed in the wrong place.");
        }

        if ("tower".equals(expectedType) || "tower".equals(actualType)) {
            hints.add("The mismatch is in the tower section. Check both its indentation and its number of lines.");
        }

        if (firstDiff < expected.size() && firstDiff < actual.size()) {
            String expNoIndent = lstrip(expected.get(firstDiff));
            String actNoIndent = lstrip(actual.get(firstDiff));

            if (expNoIndent.equals(actNoIndent) && !expected.get(firstDiff).equals(actual.get(firstDiff))) {
                hints.add("The visible characters match after removing leading spaces, so this looks like an indentation problem.");
            }
        }

        int shift = detectSingleBlockShift(expected, actual, firstDiff);
        if (shift > 0) {
            hints.add("The rest of the output matches again after one missing block, so one whole section may be missing or one loop may run too few times.");
        } else if (shift < 0) {
            hints.add("The rest of the output matches again after one extra block, so one whole section may be duplicated or one loop may run too many times.");
        }

        if (hints.isEmpty()) {
            hints.add("Compare loop bounds, indentation math, and the order of the printed sections.");
        }

        return hints;
    }

    private static void printSectionSizeReminder(int size) {
        System.out.println("\nExpected section sizes for SIZE = " + size + ":");
        System.out.println("• upper spire = " + size + " line(s)");
        System.out.println("• upper roof/base = " + size + " line(s)");
        System.out.println("• upper deck = 1 line");
        System.out.println("• bowl = " + size + " line(s)");
        System.out.println("• lower spire = " + size + " line(s)");
        System.out.println("• tower = " + (4 * size) + " line(s)");
        System.out.println("• lower roof/base = " + size + " line(s)");
        System.out.println("• lower deck = 1 line");
    }

    /* ================== LINE / SECTION HELPERS ================== */

    private static String sectionNameForLine(int size, int lineNumber) {
        int line = lineNumber;

        if (line <= 0) {
            return "before the output begins";
        }

        if (line <= size) {
            return "upper spire";
        }
        line -= size;

        if (line <= size) {
            return "upper roof/base";
        }
        line -= size;

        if (line == 1) {
            return "upper deck";
        }
        line -= 1;

        if (line <= size) {
            return "bowl";
        }
        line -= size;

        if (line <= size) {
            return "lower spire";
        }
        line -= size;

        if (line <= 4 * size) {
            return "tower";
        }
        line -= 4 * size;

        if (line <= size) {
            return "lower roof/base";
        }
        line -= size;

        if (line == 1) {
            return "lower deck";
        }

        return "after the expected output ends";
    }

    private static String lineType(String line) {
        if (line == null) {
            return "no line";
        }

        String t = lstrip(line);

        if (t.equals("/\\")) {
            return "spire";
        }
        if (t.startsWith("__/")) {
            return "roof/base";
        }
        if (t.startsWith("{")) {
            return "deck";
        }
        if (t.startsWith("\\_")) {
            return "bowl";
        }
        if (t.startsWith("|\"\"\\/\"\"|")) {
            return "tower";
        }

        return "unknown";
    }

    /* ================== UTILITIES ================== */

    private static String showSpaces(String s) {
        return s.replace(" ", "·");
    }

    private static String rstrip(String s) {
        return s.replaceAll("\\s+$", "");
    }

    private static String lstrip(String s) {
        return s.replaceFirst("^\\s+", "");
    }
}
