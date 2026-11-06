"""Automated checks for step 5 (list and get) of products.py."""

import json
import os
import subprocess
import sys
import tempfile

WORKSPACE = "/Users/nikitaxu/Viber/ISBA2438"


def run(args, cwd):
    return subprocess.run(
        [sys.executable, os.path.join(WORKSPACE, "products.py")] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def write_store(cwd, store):
    path = os.path.join(cwd, "products.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(store, handle)
    return path


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["list"], tmpdir)
    assert result.returncode == 0 and result.stdout.strip() == "[]", result
    assert not os.path.exists(os.path.join(tmpdir, "products.json"))
    print("PASS list with no file prints [] and does not create the file")

    result = run(["get", "1"], tmpdir)
    assert result.returncode == 1 and result.stdout == "" and "1" in result.stderr
    assert not os.path.exists(os.path.join(tmpdir, "products.json"))
    print("PASS get with no file reports missing ID 1 (exit 1) and creates nothing")

    for bad in ["abc", "0", "-1", "1.5"]:
        result = run(["get", bad], tmpdir)
        assert result.returncode == 2, (bad, result.returncode, result.stderr)
        assert result.stdout == ""
    print("PASS invalid IDs to get exit 2 with no stdout")

    write_store(
        tmpdir,
        {
            "next_id": 11,
            "products": [
                {"id": 10, "name": "Ten", "price": "10.00", "quantity": 1},
                {"id": 2, "name": "Two", "price": "2.00", "quantity": 2},
                {"id": 1, "name": "One", "price": "1.00", "quantity": 3},
            ],
        },
    )
    data_file = os.path.join(tmpdir, "products.json")
    before = read_bytes(data_file)

    result = run(["list"], tmpdir)
    listed = json.loads(result.stdout)
    assert [p["id"] for p in listed] == [1, 2, 10], listed
    assert listed[0] == {"id": 1, "name": "One", "price": "1.00", "quantity": 3}
    assert read_bytes(data_file) == before
    print("PASS list sorts numerically (1, 2, 10) and does not rewrite the file")

    result = run(["get", "2"], tmpdir)
    assert json.loads(result.stdout) == {"id": 2, "name": "Two", "price": "2.00", "quantity": 2}
    assert read_bytes(data_file) == before
    print("PASS get 2 prints exactly that product and leaves the file untouched")

    result = run(["get", "999"], tmpdir)
    assert result.returncode == 1 and result.stdout == "" and "999" in result.stderr
    assert read_bytes(data_file) == before
    print("PASS get 999 exits 1, names the ID on stderr, file unchanged")

    with open(data_file, "w", encoding="utf-8") as handle:
        handle.write("{oops")
    before_broken = read_bytes(data_file)
    result = run(["list"], tmpdir)
    assert result.returncode == 1 and result.stdout == ""
    assert read_bytes(data_file) == before_broken
    print("PASS list against malformed file exits 1 and leaves it unchanged")

print("ALL STEP 5 TESTS PASSED")
