"""Verifies the handout's output and exit-code contract end-to-end:
exit 0/1/2 classes, JSON-only stdout on success, stderr-only failures that
name the problem, no tracebacks, and failures that consume nothing."""

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


def check_failure(args, tmpdir, expected_code):
    result = run(args, tmpdir)
    assert result.returncode == expected_code, (args, result.returncode, result.stderr)
    assert result.stdout == "", args
    assert result.stderr.strip() != "", args
    assert "Traceback" not in result.stderr, args
    return result


def check_success_json(args, tmpdir):
    result = run(args, tmpdir)
    assert result.returncode == 0, (args, result.stderr)
    assert result.stderr == "", args
    json.loads(result.stdout)
    return result


with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")

    for args in (
        ["--help"],
        ["add", "--help"],
        ["list", "--help"],
        ["get", "--help"],
        ["update", "--help"],
        ["delete", "--help"],
        ["low-stock", "--help"],
    ):
        result = run(args, tmpdir)
        assert result.returncode == 0 and result.stdout != "", args
    assert not os.path.exists(data_file)
    print("PASS 7 help requests exit 0 with text on stdout; none touch the data file")

    check_success_json(["add", "--name", "Notebook", "--price", "4.5", "--quantity", "10"], tmpdir)
    check_success_json(["add", "--name", "Pencil", "--price", "1.25", "--quantity", "5"], tmpdir)
    check_success_json(["list"], tmpdir)
    check_success_json(["get", "1"], tmpdir)
    check_success_json(["update", "1", "--quantity", "12"], tmpdir)
    check_success_json(["low-stock", "--threshold", "5"], tmpdir)
    print("PASS successful data commands exit 0: parseable JSON on stdout, stderr empty")

    before = open(data_file, "rb").read()
    for args in (["get", "99"], ["update", "99", "--quantity", "3"], ["delete", "99", "--yes"]):
        result = check_failure(args, tmpdir, 1)
        assert "99" in result.stderr
    print("PASS missing-ID failures exit 1, name the ID, print nothing on stdout")

    bad_ids = [["get", "abc"], ["get", "0"], ["delete", "-1", "--yes"]]
    for args in bad_ids:
        check_failure(args, tmpdir, 2)
    print("PASS malformed IDs exit 2 (a syntax problem, not a missing product)")

    syntax_cases = [
        [],
        ["bogus"],
        ["--bogus"],
        ["list", "--file", "x.json"],
        ["add", "--name", "X", "--price", "1", "--quantity", "1", "--bogus"],
        ["add", "--price", "1", "--quantity", "1"],
        ["add", "--name", "X", "--price", "1.2.3", "--quantity", "1"],
        ["add", "--name", "X", "--price", "1", "--quantity", "one"],
        ["get"],
        ["get", "1", "2"],
        ["list", "extra"],
        ["update", "1"],
        ["update", "1", "--price", "abc"],
        ["delete", "1"],
        ["low-stock"],
        ["low-stock", "--threshold", "-2"],
        ["low-stock", "--threshold", "1.5"],
    ]
    for args in syntax_cases:
        check_failure(args, tmpdir, 2)
    assert open(data_file, "rb").read() == before
    print(f"PASS all {len(syntax_cases)} syntax/value errors exit 2; file byte-identical afterwards")

    with open(data_file, "w", encoding="utf-8") as handle:
        handle.write("{not json")
    corrupt_before = open(data_file, "rb").read()
    for args in (
        ["list"],
        ["get", "1"],
        ["add", "--name", "X", "--price", "1", "--quantity", "1"],
        ["update", "1", "--quantity", "2"],
        ["delete", "1", "--yes"],
        ["low-stock", "--threshold", "5"],
    ):
        check_failure(args, tmpdir, 1)
    assert open(data_file, "rb").read() == corrupt_before
    print("PASS invalid stored data: every command exits 1, stderr only, file unchanged")

    good_store = '{"next_id": 3, "products": [{"id": 1, "name": "Notebook", "price": "4.50", "quantity": 12}]}'
    with open(data_file, "w", encoding="utf-8") as handle:
        handle.write(good_store)
    os.chmod(tmpdir, 0o555)
    try:
        result = check_failure(["update", "1", "--quantity", "9"], tmpdir, 1)
        assert "cannot write" in result.stderr
    finally:
        os.chmod(tmpdir, 0o755)
    print("PASS file write failure exits 1 with an explanation, data not replaced")

    for args, expected in (
        (["add", "--name", "X", "--price", "bad", "--quantity", "1"], 2),
        (["get", "999"], 1),
        (["delete", "1"], 2),
        (["bogus"], 2),
    ):
        check_failure(args, tmpdir, expected)
    result = run(["add", "--name", "Next", "--price", "2", "--quantity", "2"], tmpdir)
    assert json.loads(result.stdout)["id"] == 3
    print("PASS failed commands consumed no ID: next successful add still got ID 3 (the saved next_id)")

print("OUTPUT AND EXIT CODES: ALL HANDOUT RULES VERIFIED")
