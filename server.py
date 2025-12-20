from flask import Flask, request, Response, send_from_directory
import os, tempfile, subprocess, shutil, re

app = Flask(__name__)
RUN_TIMEOUT = 30

REFERENCE_DIR = "reference"
REFERENCE_TXT = "SpaceNeedle.txt"

# -----------------------------
# Helpers
# -----------------------------

def normalize(text):
    return "\n".join(
        line.rstrip()
        for line in text.replace("\r\n", "\n").split("\n")
    )

def show_spaces(line):
    if line == "":
        return "(empty line)"
    return line.replace(" ", "·")

def extract_size(code):
    m = re.search(r'public\s+static\s+final\s+int\s+SIZE\s*=\s*(\d+)', code)
    return int(m.group(1)) if m else None

def load_reference_for_size(size):
    path = os.path.join(REFERENCE_DIR, REFERENCE_TXT)
    with open(path) as f:
        lines = f.read().splitlines()

    start = None
    end = None

    for i, line in enumerate(lines):
        if line.strip() == f"SIZE = {size}":
            start = i + 1
            continue
        if start is not None and line.strip().startswith("SIZE ="):
            end = i
            break

    if start is None:
        raise ValueError(f"No reference output for SIZE = {size}")

    block = lines[start:end]
    return normalize("\n".join(block))

def classify(got, exp):
    if got.strip() == exp.strip():
        return "SPACING"
    if got.replace(" ", "") == exp.replace(" ", ""):
        return "INDENTATION"
    if len(got) != len(exp):
        return "LENGTH"
    return "CONTENT"

def hint_for(kind):
    return {
        "SPACING": "Spacing mismatch. Count leading spaces carefully.",
        "INDENTATION": "Indentation error. Check how many spaces you print before symbols.",
        "LENGTH": "Line length differs. Check repeated patterns like (), [], or _.",
        "CONTENT": "Symbol or order mismatch. Compare this line carefully."
    }[kind]

# -----------------------------
# CORS
# -----------------------------

@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    return resp

# -----------------------------
# Main grading endpoint
# -----------------------------

@app.route("/run", methods=["POST", "OPTIONS"])
def run():
    if request.method == "OPTIONS":
        return Response(status=204)

    code = (request.get_json() or {}).get("code", "")

    if "class Project1" not in code:
        return Response(
            "STATUS:ERROR\n"
            "MESSAGE:File must declare `public class Project1`",
            200
        )

    size = extract_size(code)
    if size is None:
        return Response(
            "STATUS:ERROR\n"
            "MESSAGE:Could not find `public static final int SIZE = ...`",
            200
        )

    try:
        expected = load_reference_for_size(size)
    except ValueError as e:
        return Response(
            f"STATUS:ERROR\nMESSAGE:{str(e)}",
            200
        )

    tmp = tempfile.mkdtemp(prefix="p1_")

    try:
        # Write student file
        with open(os.path.join(tmp, "Project1.java"), "w") as f:
            f.write(re.sub(r'^\s*package\s+.*?;\s*', '', code, flags=re.MULTILINE))

        # Compile
        cs = subprocess.run(
            ["javac", "Project1.java"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT
        )
        if cs.returncode != 0:
            return Response(
                "STATUS:COMPILE_ERROR\n" + cs.stderr,
                200
            )

        # Run
        runp = subprocess.run(
            ["java", "Project1"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT
        )

        student = normalize(runp.stdout)
        expected = normalize(expected)

        s_lines = student.split("\n")
        r_lines = expected.split("\n")

        # Line count mismatch
        if len(s_lines) != len(r_lines):
            diff = len(s_lines) - len(r_lines)
            return Response(
                "STATUS:LINE_COUNT\n"
                f"EXPECTED:{len(r_lines)}\n"
                f"GOT:{len(s_lines)}\n"
                "HINT:Your program printed "
                f"{'too many' if diff > 0 else 'too few'} lines. "
                "Check loop bounds involving SIZE.",
                200
            )

        # Line-by-line comparison
        for i, (g, e) in enumerate(zip(s_lines, r_lines), start=1):
            if g != e:
                kind = classify(g, e)
                return Response(
                    "STATUS:MISMATCH\n"
                    f"TYPE:{kind}\n"
                    f"LINE:{i}\n"
                    f"EXPECTED:{show_spaces(e)}\n"
                    f"GOT:{show_spaces(g)}\n"
                    f"HINT:{hint_for(kind)}",
                    200
                )

        return Response("STATUS:PASS", 200)

    except subprocess.TimeoutExpired:
        return Response(
            "STATUS:TIMEOUT\n"
            "HINT:Your program took too long. Check for infinite loops.",
            200
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# -----------------------------
# Frontend
# -----------------------------

@app.get("/")
def index():
    return send_from_directory(".", "index.html")

# -----------------------------
# Entry point
# -----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
