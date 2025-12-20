from flask import Flask, request, Response, send_from_directory
import os, tempfile, subprocess, shutil, re

app = Flask(__name__)

# ================= CONFIG =================

TESTER_FILE = "Project1LocalTester.java"
REFERENCE_FILE = "SpaceNeedle.txt"
RUN_TIMEOUT = int(os.environ.get("RUN_TIMEOUT", "30"))

# ================= CORS =================

@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    return resp

# ================= ROUTES =================

@app.route("/run", methods=["POST", "OPTIONS"])
def run_tests():
    if request.method == "OPTIONS":
        return Response(status=204)

    data = request.get_json(silent=True) or {}
    code = data.get("code", "")

    # Enforce correct class
    if "class Project1" not in code:
        return Response(
            "❌ Error: File must contain `public class Project1`.",
            200,
            mimetype="text/plain"
        )

    # Strip package statements
    code = re.sub(r'^\s*package\s+.*?;\s*', '', code, flags=re.MULTILINE)

    tmp = tempfile.mkdtemp(prefix="p1_")

    try:
        # Write student file
        with open(os.path.join(tmp, "Project1.java"), "w", encoding="utf-8") as f:
            f.write(code)

        # Copy tester + reference
        shutil.copy(TESTER_FILE, os.path.join(tmp, TESTER_FILE))
        shutil.copy(REFERENCE_FILE, os.path.join(tmp, REFERENCE_FILE))

        # Compile (tester compiles Project1 internally)
        compile_proc = subprocess.run(
            ["javac", TESTER_FILE, "Project1.java"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT
        )

        if compile_proc.returncode != 0:
            msg = "❌ Compilation failed.\n\n"
            if compile_proc.stderr:
                msg += "STDERR:\n" + compile_proc.stderr + "\n"
            if compile_proc.stdout:
                msg += "STDOUT:\n" + compile_proc.stdout + "\n"
            return Response(msg, 200, mimetype="text/plain")

        # Run tester
        run_proc = subprocess.run(
            ["java", "Project1LocalTester"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT
        )

        output = (run_proc.stdout or "")
        if run_proc.stderr:
            output += "\n" + run_proc.stderr

        return Response(output, 200, mimetype="text/plain")

    except subprocess.TimeoutExpired:
        return Response("⏱️ Execution timed out.", 200, mimetype="text/plain")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ================= STATIC =================

@app.get("/")
def index():
    return send_from_directory(".", "index.html")

@app.get("/healthz")
def healthz():
    return "ok", 200

# ================= MAIN =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
