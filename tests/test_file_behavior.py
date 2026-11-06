"""Verifies the handout's file-behavior rules end-to-end: missing-file handling,
creation rules, read-only inertness, --file paths, corrupt stores, and write
failures (simulated with chmod) that must not replace existing data."""

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


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")

    result = run(["list"], tmpdir)
    result2 = run(["low-stock", "--threshold", "9"], tmpdir)
    result3 = run(["get", "1"], tmpdir)
    result4 = run(["update", "1", "--quantity", "2"], tmpdir)
    result5 = run(["delete", "1", "--yes"], tmpdir)
    assert result.returncode == 0 and result.stdout.strip() == "[]"
    assert result2.returncode == 0 and result2.stdout.strip() == "[]"
    assert result3.returncode == 1 and "1" in result3.stderr
    assert result4.returncode == 1 and "1" in result4.stderr
    assert result5.returncode == 1 and "1" in result5.stderr
    assert not os.path.exists(data_file)
    print("PASS missing file = empty store: list/low-stock -> [], get/update/delete report ID 1; no file created")

    result = run(["add", "--name", "A", "--price", "1", "--quantity", "1"], tmpdir)
    assert result.returncode == 0 and os.path.exists(data_file)
    print("PASS the first successful add created products.json")

    before = read_bytes(data_file)
    for args in (["list"], ["get", "1"], ["low-stock", "--threshold", "5"]):
        result = run(args, tmpdir)
        assert result.returncode == 0, args
    assert read_bytes(data_file) == before
    print("PASS list, get, low-stock leave the file byte-identical (never rewritten)")

    result = run(["update", "1", "--quantity", "7"], tmpdir)
    assert json.loads(result.stdout)["quantity"] == 7
    result = run(["get", "1"], tmpdir)
    assert json.loads(result.stdout)["quantity"] == 7
    print("PASS a later invocation sees saved changes (save happened before success was printed)")

with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["--file", "newdir/store.json", "add", "--name", "A", "--price", "1", "--quantity", "1"], tmpdir)
    assert result.returncode == 1 and result.stdout == ""
    assert "cannot write" in result.stderr
    assert not os.path.exists(os.path.join(tmpdir, "newdir"))
    print("PASS --file into a missing parent directory: exit 1, directory NOT created")

    os.mkdir(os.path.join(tmpdir, "data"))
    result = run(["--file", "data/store.json", "add", "--name", "A", "--price", "1", "--quantity", "1"], tmpdir)
    assert result.returncode == 0
    assert os.path.exists(os.path.join(tmpdir, "data", "store.json"))
    print("PASS relative --file paths resolve from the current directory")

with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")
    corrupt_states = {
        "empty file": "",
        "whitespace only": "  \n  ",
        "malformed JSON": '{"next_id": 2, "products": [',
        "not an object": '"just a string"',
    }
    for label, text in corrupt_states.items():
        with open(data_file, "w", encoding="utf-8") as handle:
            handle.write(text)
        before = read_bytes(data_file)
        result = run(["list"], tmpdir)
        assert result.returncode == 1 and result.stdout == "", (label, result)
        assert read_bytes(data_file) == before
        print(f"PASS {label}: exit 1, no stdout, file byte-identical")

with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["add", "--name", "A", "--price", "1", "--quantity", "1"], tmpdir)
    data_file = os.path.join(tmpdir, "products.json")
    before = read_bytes(data_file)

    os.chmod(tmpdir, 0o555)
    try:
        result = run(["update", "1", "--quantity", "9"], tmpdir)
        assert result.returncode == 1 and result.stdout == ""
        assert "cannot write" in result.stderr
        assert read_bytes(data_file) == before
        print("PASS write failure (read-only directory): exit 1, message, existing data NOT replaced")
    finally:
        os.chmod(tmpdir, 0o755)

print("FILE BEHAVIOR: ALL HANDOUT RULES VERIFIED")
