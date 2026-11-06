"""Verifies unusually long digit strings for price, quantity, threshold, and ID
are handled exactly like short ones: accepted when valid, rejected cleanly when
the product is missing, no tracebacks, no length restrictions."""

import json
import os
import subprocess
import sys
import tempfile

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

WORKSPACE = "/Users/nikitaxu/Viber/ISBA2438"


def run(args, cwd):
    return subprocess.run(
        [sys.executable, os.path.join(WORKSPACE, "products.py")] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


LONG_PRICE = "9" * 5000
LONG_QTY = "5" * 5000
LONG_ID = "7" * 5000

with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["add", "--name", "A", "--price", LONG_PRICE, "--quantity", "1"], tmpdir)
    assert result.returncode == 0, result.stderr[-300:]
    assert json.loads(result.stdout)["price"] == LONG_PRICE + ".00"
    print("PASS 5000-digit price accepted and stored with two decimals")

    result = run(["add", "--name", "B", "--price", "1", "--quantity", LONG_QTY], tmpdir)
    assert result.returncode == 0, result.stderr[-300:]
    assert json.loads(result.stdout)["quantity"] == int(LONG_QTY)
    print("PASS 5000-digit quantity accepted and saved exactly")

    result = run(["get", "1"], tmpdir)
    assert json.loads(result.stdout)["price"] == LONG_PRICE + ".00"
    print("PASS a later invocation reads the long price back from the file")

    result = run(["update", "1", "--quantity", LONG_QTY], tmpdir)
    assert result.returncode == 0, result.stderr[-300:]
    print("PASS 5000-digit quantity via update accepted and saved")

    result = run(["low-stock", "--threshold", LONG_QTY], tmpdir)
    assert [p["id"] for p in json.loads(result.stdout)] == [1, 2]
    print("PASS 5000-digit threshold still compares correctly (both products <=)")

    result = run(["low-stock", "--threshold", "0"], tmpdir)
    assert json.loads(result.stdout) == []
    print("PASS normal matching unaffected (threshold 0 -> [])")

    result = run(["get", LONG_ID], tmpdir)
    assert result.returncode == 1 and result.stdout == ""
    assert "Traceback" not in result.stderr
    assert LONG_ID in result.stderr
    print("PASS 5000-digit ID is a valid positive integer: exit 1 not-found, ID named in the message")

    data_file = os.path.join(tmpdir, "products.json")
    crafted = {
        "next_id": int(LONG_ID),
        "products": [json.loads(run(["get", "1"], tmpdir).stdout)],
    }
    with open(data_file, "w", encoding="utf-8") as handle:
        json.dump(crafted, handle)
    result = run(["list"], tmpdir)
    assert result.returncode == 0, result.stderr[-300:]
    print("PASS a stored next_id with 5000 digits loads and lists fine")

    result = run(["add", "--name", "C", "--price", "2", "--quantity", "2"], tmpdir)
    assert json.loads(result.stdout)["id"] == int(LONG_ID)
    print("PASS the next add consumes the huge next_id exactly (+1)")

print("LONG NUMBERS: ALL CASES HANDLED")
