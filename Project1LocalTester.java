import java.io.*;
import java.util.*;

public class Project1LocalTester {

    /* ================== CONFIG ================== */

    // Turn on to see every line comparison
    private static final boolean DEBUG = true;

    /* ================== MAIN ================== */

    public static void main(String[] args) throws Exception {
        System.out.println("=== TCSS 142 · Project 1 TA Tester ===\n");

        // Force compilation to avoid stale .class files (CRITICAL)
        forceCompile();

        int size = detectSize();
        if (size == -1) {
            System.out.println("❌ Could not detect SIZE constant in Project1.java");
            return;
        }

        List<String> expected = loadReference(size);
        List<String> actual = runStudent();

        if (expected.isEmpty()) {
            System.out.println("❌ No reference output found for SIZE = " + size);
            return;
        }

        if (actual.size() != expected.size()) {
            reportLineCount(size, expected, actual);
            return;
        }

        for (int i = 0; i < expected.size(); i++) {
            if (DEBUG) {
                System.out.printf(
                        "[DEBUG] Line %2d | expected=%s | actual=%s%n",
                        i + 1,
                        showSpaces(expected.get(i)),
                        showSpaces(actual.get(i))
                );
            }

            if (!expected.get(i).equals(actual.get(i))) {
                reportMismatch(size, i + 1, expected.get(i), actual.get(i));
                return;
            }
        }

        System.out.println("✅ PASS (SIZE = " + size + ")");
    }

    /* ================== EXECUTION ================== */

    private static void forceCompile() throws Exception {
        Process compile = new ProcessBuilder("javac", "Project1.java")
                .redirectErrorStream(true)
                .start();

        compile.waitFor();
    }

    private static List<String> runStudent() throws Exception {
        Process p = new ProcessBuilder("java", "Project1")
                .redirectErrorStream(true)
                .start();

        List<String> out = new ArrayList<>();
        try (BufferedReader br =
                     new BufferedReader(new InputStreamReader(p.getInputStream()))) {
            String line;
            while ((line = br.readLine()) != null) {
                out.add(rstrip(line));
            }
        }
        return out;
    }

    private static int detectSize() throws Exception {
        try (Scanner sc = new Scanner(new File("Project1.java"))) {
            while (sc.hasNextLine()) {
                String line = sc.nextLine();
                if (line.contains("static final int SIZE")) {
                    return Integer.parseInt(line.replaceAll("\\D+", ""));
                }
            }
        }
        return -1;
    }

    /* ================== REFERENCE LOADING ================== */

    private static List<String> loadReference(int size) throws Exception {
        List<String> ref = new ArrayList<>();
        boolean active = false;

        File f = new File("SpaceNeedle.txt");
        if (!f.exists()) {
            System.out.println("❌ Missing SpaceNeedle.txt");
            System.out.println("Place SpaceNeedle.txt in the same directory as the tester.");
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

                    // 🔧 CRITICAL FIX: ignore blank lines
                    if (!trimmed.isEmpty()) {
                        ref.add(trimmed);
                    }
                }
            }
        }

        return ref;
    }

    /* ================== ERROR REPORTING ================== */

    private static void reportLineCount(int size,
                                        List<String> expected,
                                        List<String> actual) {

        System.out.println("❌ LINE COUNT MISMATCH (SIZE = " + size + ")");
        System.out.println("Expected: " + expected.size());
        System.out.println("Actual:   " + actual.size());

        System.out.println("\n--- Expected (last lines) ---");
        printTail(expected);

        System.out.println("\n--- Actual (last lines) ---");
        printTail(actual);

        System.out.println("\n💡 Likely causes:");
        System.out.println("• A structural section is missing or duplicated");
        System.out.println("• A loop ran too many or too few times");
        System.out.println("• Method call order in main() is incorrect");
        System.out.println("• Beam section must be exactly 4 × SIZE lines");
    }

    private static void reportMismatch(int size,
                                       int line,
                                       String exp,
                                       String got) {

        System.out.println("❌ OUTPUT MISMATCH (SIZE = " + size + ")");
        System.out.println("First difference at line " + line);

        System.out.println("\nExpected:");
        System.out.println(showSpaces(exp));

        System.out.println("\nActual:");
        System.out.println(showSpaces(got));

        System.out.println("\n💡 Likely issue:");
        if (exp.stripLeading().equals(got.stripLeading())) {
            System.out.println("• Indentation mismatch (wrong number of spaces)");
        } else {
            System.out.println("• Characters or structure differ");
        }
    }

    /* ================== UTILITIES ================== */

    private static void printTail(List<String> lines) {
        for (int i = Math.max(0, lines.size() - 6); i < lines.size(); i++) {
            System.out.println(showSpaces(lines.get(i)));
        }
    }

    private static String showSpaces(String s) {
        return s.replace(" ", "·");
    }

    private static String rstrip(String s) {
        return s.replaceAll("\\s+$", "");
    }
}
