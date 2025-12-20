from flask import Flask, request, Response, send_from_directory
import os, tempfile, subprocess, shutil, re

app = Flask(__name__)

# =========================
# Configuration
# =========================
RUN_TIMEOUT = 30
REFERENCE_FILE = "Project1_reference.java"

# =========================
# CORS (needed for browser fetch)
# =========================
@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    return resp

# =========================
# Utilities
# =========================
def normalize(text: str) -> str:
    """
    Normalize output so comparisons are fair:
    - Windows -> Unix newlines
    - Remove trailing whitespace ONLY
    - Preserve leading spaces
    """
    return "\n".join(
        line.rstrip()
        for line in text.replace("\r\n", "\n").split("\n")
    )

# =========================
# Main test endpoint
# =========================
@app.route("/run", methods=["POST", "OPTIONS"])
def run():
    if request.method == "OPTIONS":
        return Response(status=204)

    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")

    # ---- Basic validation ----
    if not code.strip():
        return Response(
            "STATUS:ERROR\nMESSAGE:No code provided.",
            200,
            mimetype="text/plain"
        )

    if "class Project1" not in code:
        return Response(
            "STATUS:ERROR\nMESSAGE:File must declare `public class Project1`.",
            200,
            mimetype="text/plain"
        )

    # Remove any package declaration
    code = re.sub(r'^\s*package\s+.*?;\s*', '', code, flags=re.MULTILINE)

    tmp = tempfile.mkdtemp(prefix="p1_")

    try:
        # ---- Write student file ----
        with open(os.path.join(tmp, "Project1.java"), "w", encoding="utf-8") as f:
            f.write(code)

        # ---- Copy reference solution ----
        shutil.copy(
            os.path.join("reference", REFERENCE_FILE),
            os.path.join(tmp, "Project1_reference.java")
        )

        # ---- Compile student code ----
        compile_student = subprocess.run(
            ["javac", "Project1.java"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT
        )

        if compile_student.returncode != 0:
            return Response(
                "STATUS:COMPILE_ERROR\nDETAILS:\n" + compile_student.stderr,
                200,
                mimetype="text/plain"
            )

        # ---- Compile reference ----
        subprocess.run(
            ["javac", "Project1_reference.java"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT
        )

        # ---- Run both programs ----
        student_run = subprocess.run(
            ["java", "Project1"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT
        )

        reference_run = subprocess.run(
            ["java", "Project1_reference"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT
        )

        student_out = normalize(student_run.stdout or "")
        expected_out = normalize(reference_run.stdout or "")

        student_lines = student_out.split("\n")
        expected_lines = expected_out.split("\n")

        # ---- Line count mismatch ----
        if len(student_lines) != len(expected_lines):
            return Response(
                f"STATUS:LINE_COUNT\nEXPECTED:{len(expected_lines)}\nGOT:{len(student_lines)}",
                200,
                mimetype="text/plain"
            )

        # ---- Line-by-line comparison ----
        for i, (s, e) in enumerate(zip(student_lines, expected_lines), start=1):
            if s != e:
                return Response(
                    "STATUS:MISMATCH\n"
                    f"LINE:{i}\n"
                    f"EXPECTED:{e}\n"
                    f"GOT:{s}",
                    200,
                    mimetype="text/plain"
                )

        # ---- Perfect match ----
        return Response("STATUS:PASS", 200, mimetype="text/plain")

    except subprocess.TimeoutExpired:
        return Response(
            "STATUS:TIMEOUT\nMESSAGE:Program took too long to run.",
            200,
            mimetype="text/plain"
        )

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# =========================
# Frontend + health
# =========================
@app.get("/")
def index():
    return send_from_directory(".", "index.html")

@app.get("/healthz")
def healthz():
    return "ok", 200

# =========================
# App entry point (CRITICAL)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
