from flask import Flask, request, Response, send_from_directory
import os, tempfile, subprocess, shutil, re

app = Flask(__name__)

RUN_TIMEOUT = 30

REFERENCE_DIR = "reference"
REFERENCE_TXT = "SpaceNeedle.txt"

# Sizes to validate
TEST_SIZES = [1, 2, 3, 4]


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp


# ------------------------------------------------------------
# NORMALIZATION RULES
#  • ignore blank lines
#  • ignore ALL spaces
#  • compare symbols only
# ------------------------------------------------------------
def normalize(text):
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if line == "":
            continue
        out.append(line.replace(" ", ""))
    return out


def load_reference(size):
    path = os.path.join(REFERENCE_DIR, REFERENCE_TXT)
    if not os.path.exists(path):
        raise RuntimeError("SpaceNeedle.txt not found")

    lines = open(path).read().splitlines()

    block = []
    active = False
    for line in lines:
        if line.strip() == f"SIZE = {size}":
            active = True
            block.clear()
            continue
        if active and line.strip().startswith("SIZE ="):
            break
        if active:
            clean = line.strip()
            if clean != "":
                block.append(clean.replace(" ", ""))

    return block


# 🔧 SAFE SIZE REWRITE (NO REGEX CRASHES)
def rewrite_size(code, size):
    return re.sub(
        r"(public\s+static\s+final\s+int\s+SIZE\s*=\s*)\d+",
        lambda m: m.group(1) + str(size),
        code
    )


@app.route("/run", methods=["POST", "OPTIONS"])
def run():
    if request.method == "OPTIONS":
        return Response(status=204)

    payload = request.get_json() or {}
    code = payload.get("code", "")

    if "class Project1" not in code:
        return Response(
            "STATUS:COMPILE_ERROR\n"
            "DETAILS: File must declare `public class Project1`",
            200
        )

    tmp = tempfile.mkdtemp(prefix="p1_")

    try:
        for size in TEST_SIZES:
            modified = rewrite_size(code, size)

            # Remove package if student added one
            modified = re.sub(
                r'^\s*package\s+.*?;\s*',
                '',
                modified,
                flags=re.MULTILINE
            )

            with open(os.path.join(tmp, "Project1.java"), "w") as f:
                f.write(modified)

            # Compile
            compile_proc = subprocess.run(
                ["javac", "Project1.java"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT
            )

            if compile_proc.returncode != 0:
                return Response(
                    "STATUS:COMPILE_ERROR\nDETAILS:\n" +
                    compile_proc.stderr,
                    200
                )

            # Run
            run_proc = subprocess.run(
                ["java", "Project1"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT
            )

            student = normalize(run_proc.stdout)
            reference = load_reference(size)

            # ---------- LINE COUNT ----------
            if len(student) != len(reference):
                return Response(
                    "STATUS:LINE_COUNT\n"
                    f"SIZE:{size}\n\n"
                    f"Expected: {len(reference)} lines\n"
                    f"Your output: {len(student)} lines\n\n"
                    "Why this happens:\n"
                    "Your output is missing or duplicating a structural section.\n\n"
                    "Expected ending:\n" +
                    "\n".join(reference[-6:]) +
                    "\n\nYour output ending:\n" +
                    "\n".join(student[-6:]),
                    200
                )

            # ---------- CONTENT ----------
            for i, (a, b) in enumerate(zip(student, reference), start=1):
                if a != b:
                    return Response(
                        "STATUS:MISMATCH\n"
                        f"SIZE:{size}\n"
                        f"LINE:{i}\n\n"
                        "Expected:\n" + b + "\n\n"
                        "Your output:\n" + a + "\n\n"
                        "Hint:\n"
                        "Symbols on this line do not match. "
                        "Spacing and indentation are ignored.",
                        200
                    )

        return Response("STATUS:PASS", 200)

    except subprocess.TimeoutExpired:
        return Response(
            "STATUS:TIMEOUT\n"
            "DETAILS: Program took too long (possible infinite loop).",
            200
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
