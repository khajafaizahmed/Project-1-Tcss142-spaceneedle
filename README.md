# TCSS 142 – Project 1 Space Needle Tester

> **Status: offline.** This tester was used for a past TCSS 142 offering and is switched off.
> The page still loads, but `/run` returns *503 – tester offline* until it is turned back on.

## Turning it back on

The tester only runs code when the environment variable `TESTER_ENABLED=true` is set.

1. In the hosting dashboard (Render → this service → **Environment**), add `TESTER_ENABLED` = `true`.
2. Save and redeploy (or **Resume** the service if it was suspended).
3. To switch it off again, delete the variable (or set it to `false`) and redeploy.

Running locally: `TESTER_ENABLED=true python server.py`

Optional: `JAVA_MAX_HEAP` (default `256m`) caps memory for submitted code.

**Before you turn it on, keep in mind:** this service compiles and runs whatever Java is posted to `/run`.
The limits here (30 s timeout, memory cap, 200 KB request cap, non-root container user) reduce the damage,
but submitted code can still read the container's environment variables and make network requests.
Don't put secrets in this service's environment, and switch it off again when the class ends.

Unofficial helper tester for TCSS 142 Project 1.

## What this does
- Compiles student Project1.java
- Runs it and captures output
- Runs instructor reference solution
- Compares output line-by-line
- Reports first mismatch or full pass

## What this does NOT do
- Does not reveal reference output
- Does not provide solutions
- Does not grade officially

## Usage
1. Paste Project1.java
2. Click Run Tests
3. Fix mismatches until passing

Built and maintained by TA Faiz Ahmed.
