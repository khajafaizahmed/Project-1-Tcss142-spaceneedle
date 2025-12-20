from flask import Flask, request, Response, send_from_directory
import os, tempfile, subprocess, shutil, re

app = Flask(__name__)
RUN_TIMEOUT = 30
REFERENCE_FILE = "Project1_reference.java"

@app.after_request
def cors(resp):
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
def run():
    if request.method == "OPTIONS":
        return Response(status=204)

    code = (request.get_json() or {}).get("code", "")

    if "class Project1" not in code:
        return Response(
            "STATUS:ERROR\nMESSAGE:File must declare `public class Project1`",
            200
        )

    code = re.sub(r'^\s*package\s+.*?;\s*', '', code, flags=re.MULTILINE)
    tmp = tempfile.mkdtemp(prefix="p1_")

    try:
        with open(os.path.join(tmp, "Project1.java"), "w") as f:
            f.write(code)

        shutil.copy(
            os.path.join("reference", REFERENCE_FILE),
            os.path.join(tmp, "Project1_reference.java")
        )

        # Compile student
        cs = subprocess.run(
            ["javac", "Project1.java"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )
        if cs.returncode != 0:
            return Response(
                "STATUS:COMPILE_ERROR\nDETAILS:\n" + cs.stderr,
                200
            )

        # Compile reference
        subprocess.run(
            ["javac", "Project1_reference.java"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )

        # Run both
        s = subprocess.run(
            ["java", "Project1"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )
        r = subprocess.run(
            ["java", "Project1_reference"],
            cwd=tmp, capture_output=True, text=True, timeout=RUN_TIMEOUT
        )

        s_out = normalize(s.stdout)
        r_out = normalize(r.stdout)

        s_lines = s_out.split("\n")
        r_lines = r_out.split("\n")

        if len(s_lines) != len(r_lines):
            return Response(
                f"STATUS:LINE_COUNT\nEXPECTED:{len(r_lines)}\nGOT:{len(s_lines)}",
                200
            )

        for i, (a, b) in enumerate(zip(s_lines, r_lines), start=1):
            if a != b:
                return Response(
                    "STATUS:MISMATCH\n"
                    f"LINE:{i}\n"
                    f"EXPECTED:{b}\n"
                    f"GOT:{a}",
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
