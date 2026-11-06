"""Automated checks for step 4 (add command) of products.py."""

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


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["add", "--name", "Notebook", "--price", "4.5", "--quantity", "10"], tmpdir)
    assert result.returncode == 0, (result.returncode, result.stderr)
    product = json.loads(result.stdout)
    assert product == {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 10}, product
    data_file = os.path.join(tmpdir, "products.json")
    assert json.loads(read(data_file)) == {"next_id": 2, "products": [product]}
    print("PASS first add creates the file, prints the product, saved next_id is 2")

    result = run(["add", "--name", "Pencil", "--price", "1.25", "--quantity", "5"], tmpdir)
    assert result.returncode == 0, result.stderr
    second = json.loads(result.stdout)
    assert second["id"] == 2, second
    assert json.loads(read(data_file))["next_id"] == 3
    print("PASS later invocation sees saved data; second add gets ID 2, next_id 3")

    before = read(data_file)
    bad_cases = [
        ["add", "--name", "X", "--price", "+4", "--quantity", "1"],
        ["add", "--name", "   ", "--price", "1", "--quantity", "1"],
        ["add", "--name", "", "--price", "1", "--quantity", "1"],
        ["add", "--name", "X", "--price", "1", "--quantity", "-1"],
        ["add", "--name", "X", "--price", "1", "--quantity", "1.5"],
        ["add", "--name", "X", "--price", "4.500", "--quantity", "1"],
        ["add", "--name", "X", "--price", "1"],
        ["add", "--price", "1", "--quantity", "1"],
    ]
    for case in bad_cases:
        result = run(case, tmpdir)
        assert result.returncode == 2, (case, result.returncode, result.stderr)
        assert result.stdout == "", (case, result.stdout)
        assert result.stderr.strip() != "", case
    assert read(data_file) == before
    print(f"PASS {len(bad_cases)} invalid add inputs -> exit 2, stderr only, file unchanged")

    result = run(["add", "--name", "Zero", "--price", "0", "--quantity", "0"], tmpdir)
    zero = json.loads(result.stdout)
    assert zero == {"id": 3, "name": "Zero", "price": "0.00", "quantity": 0}, zero
    print('PASS quantity 0 and price "0.00" accepted')

    result = run(["add", "--name", "  Trimmed  ", "--price", "2", "--quantity", "1"], tmpdir)
    assert json.loads(result.stdout)["name"] == "Trimmed"
    print("PASS name is trimmed before saving")

    broken = os.path.join(tmpdir, "broken.json")
    with open(broken, "w", encoding="utf-8") as handle:
        handle.write("{not json")
    before_broken = read(broken)
    result = run(
        ["--file", "broken.json", "add", "--name", "X", "--price", "1", "--quantity", "1"],
        tmpdir,
    )
    assert result.returncode == 1, result.returncode
    assert result.stdout == ""
    assert "products.py: error:" in result.stderr
    assert read(broken) == before_broken
    print("PASS add against malformed file exits 1, message on stderr, file unchanged")

    result = run(
        ["--file", "no_such_dir/new.json", "add", "--name", "X", "--price", "1", "--quantity", "1"],
        tmpdir,
    )
    assert result.returncode == 1, result.returncode
    assert not os.path.exists(os.path.join(tmpdir, "no_such_dir"))
    print("PASS write failure into missing directory exits 1 and creates nothing")

print("ALL STEP 4 TESTS PASSED")
