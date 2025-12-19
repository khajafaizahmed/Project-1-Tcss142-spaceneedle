from flask import Flask, request, Response, send_from_directory
import os, tempfile, subprocess, shutil, re

app = Flask(__name__)

RUN_TIMEOUT = 30  # seconds
REFERENCE_FILE = "Project1_reference.java"

@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    return resp

def normalize(text):
    return "\n".join(
        line.rstrip()
        for line in text.replace("\r\n", "\n").split("\n")
    )

@app.route("/run", methods=["POST", "OPTIONS"])
def run_tests():
    if request.method == "OPTIONS":
        return Response(status=204)

    data = request.get_json(silent=True) or {}
    code = data.get("code", "")

    if "class Project1" not in code:
        return Response("Error: File must define class Project1.", 200)

    # Strip package lines if present
    code = re.sub(r'^\s*package\s+.*?;\s*', '', code, flags=re.MULTILINE)

    tmp = tempfile.mkdtemp(prefix="p1_")

    try:
        # Write student file
        with open(os.path.join(tmp, "Project1.java"), "w", encoding="utf-8") as f:
            f.write(code)

        # Copy teacher reference
        shutil.copy(
            os.path.join("reference", REFERENCE_FILE),
            os.path.join(tmp, "Project1_reference.java")
        )

        # Compile student
        comp_student = subprocess.run(
            ["javac", "Project1.java"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )
        if comp_student.returncode != 0:
            return Response(
                "Compilation failed.\n\n" + comp_student.stderr,
                200, mimetype="text/plain"
            )

        # Compile reference
        comp_ref = subprocess.run(
            ["javac", "Project1_reference.java"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )
        if comp_ref.returncode != 0:
            return Response(
                "Internal reference compilation failed.",
                200, mimetype="text/plain"
            )

        # Run student
        run_student = subprocess.run(
            ["java", "Project1"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )

        # Run reference
        run_ref = subprocess.run(
            ["java", "Project1_reference"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )

        student_out = normalize(run_student.stdout or "")
        expected_out = normalize(run_ref.stdout or "")

        s_lines = student_out.split("\n")
        e_lines = expected_out.split("\n")

        if len(s_lines) != len(e_lines):
            return Response(
                f"Line count mismatch.\nExpected {len(e_lines)} lines, got {len(s_lines)}.",
                200, mimetype="text/plain"
            )

        for i, (s, e) in enumerate(zip(s_lines, e_lines), start=1):
            if s != e:
                return Response(
                    f"Mismatch at line {i}\n"
                    f"Expected: {e!r}\n"
                    f"Got:      {s!r}",
                    200, mimetype="text/plain"
                )

        return Response("All checks passed.", 200, mimetype="text/plain")

    except subprocess.TimeoutExpired:
        return Response("⏱️ Execution timed out.", 200, mimetype="text/plain")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/")
def index():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
