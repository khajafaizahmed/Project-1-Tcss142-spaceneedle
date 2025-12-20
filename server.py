from flask import Flask, request, Response, send_from_directory
import os, tempfile, subprocess, shutil, re

app = Flask(__name__)
RUN_TIMEOUT = 30

REFERENCE_DIR = "reference"
REFERENCE_TXT = "SpaceNeedle.txt"

@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp

def normalize(text):
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n"))

def extract_size(code):
    m = re.search(r"SIZE\s*=\s*(\d+)", code)
    return int(m.group(1)) if m else None

def load_reference(size):
    path = os.path.join(REFERENCE_DIR, REFERENCE_TXT)
    with open(path) as f:
        lines = f.read().splitlines()

    block = []
    active = False
    for line in lines:
        if line.strip() == f"SIZE = {size}":
            active = True
            block = []
            continue
        if active:
            if line.strip().startswith("SIZE ="):
                break
            block.append(line.rstrip())

    return block

@app.route("/run", methods=["POST", "OPTIONS"])
def run():
    if request.method == "OPTIONS":
        return Response(status=204)

    code = (request.get_json() or {}).get("code", "")

    if "class Project1" not in code:
        return Response(
            "STATUS:COMPILE_ERROR\nDETAILS:File must declare public class Project1",
            200
        )

    size = extract_size(code)
    if size is None:
        return Response(
            "STATUS:COMPILE_ERROR\nDETAILS:SIZE constant not found",
            200
        )

    tmp = tempfile.mkdtemp(prefix="p1_")
    try:
        with open(os.path.join(tmp, "Project1.java"), "w") as f:
            f.write(re.sub(r'^\s*package\s+.*?;\s*', '', code, flags=re.MULTILINE))

        cs = subprocess.run(
            ["javac", "Project1.java"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )
        if cs.returncode != 0:
            return Response(
                "STATUS:COMPILE_ERROR\nDETAILS:\n" + cs.stderr,
                200
            )

        run = subprocess.run(
            ["java", "Project1"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )

        student = normalize(run.stdout).split("\n")
        reference = load_reference(size)

        if len(student) != len(reference):
            hint = "A structural section of the Space Needle did not print."

            if student and reference:
                if reference[-1].startswith("{") and not student[-1].startswith("{"):
                    hint = (
                        "The output ends before the final window band. "
                        "This means the last structural section never printed."
                    )

            return Response(
                "STATUS:LINE_COUNT\n"
                f"EXPECTED_COUNT:{len(reference)}\n"
                f"GOT_COUNT:{len(student)}\n"
                f"HINT:{hint}\n"
                "EXPECTED_OUTPUT:\n" + "\n".join(reference) + "\n"
                "GOT_OUTPUT:\n" + "\n".join(student),
                200
            )

        for i, (a, b) in enumerate(zip(student, reference), start=1):
            if a != b:
                hint = (
                    "Indentation differs. Check how many spaces are printed."
                    if a.lstrip() == b.lstrip()
                    else "Characters or spacing differ on this line."
                )
                return Response(
                    "STATUS:MISMATCH\n"
                    f"LINE:{i}\n"
                    f"EXPECTED:{b}\n"
                    f"GOT:{a}\n"
                    f"HINT:{hint}",
                    200
                )

        return Response("STATUS:PASS", 200)

    except subprocess.TimeoutExpired:
        return Response("STATUS:TIMEOUT", 200)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

@app.get("/")
def index():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
