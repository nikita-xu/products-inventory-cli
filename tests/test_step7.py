"""Automated checks for step 7 (delete) of products.py."""

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


def setup(tmpdir):
    for name, price, quantity in [("Notebook", "4.5", 10), ("Pencil", "1.25", 5)]:
        result = run(["add", "--name", name, "--price", price, "--quantity", str(quantity)], tmpdir)
        assert result.returncode == 0, result.stderr
    return os.path.join(tmpdir, "products.json")


with tempfile.TemporaryDirectory() as tmpdir:
    data_file = setup(tmpdir)

    result = run(["delete", "2", "--yes"], tmpdir)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"deleted_id": 2}, result.stdout
    store = json.loads(open(data_file, encoding="utf-8").read())
    assert store == {
        "next_id": 3,
        "products": [{"id": 1, "name": "Notebook", "price": "4.50", "quantity": 10}],
    }, store
    print("PASS delete 2 --yes prints {\"deleted_id\": 2}, keeps product 1 and next_id 3")

    before = read_bytes(data_file)
    result = run(["delete", "1"], tmpdir)
    assert result.returncode == 2 and result.stdout == "" and "--yes" in result.stderr
    assert read_bytes(data_file) == before
    print("PASS delete without --yes exits 2 and the file is unchanged")

    result = run(["delete", "999", "--yes"], tmpdir)
    assert result.returncode == 1 and result.stdout == "" and "999" in result.stderr
    assert read_bytes(data_file) == before
    print("PASS delete of missing ID exits 1, names the ID, file unchanged")

    for bad in ["abc", "0", "-1"]:
        result = run(["delete", bad, "--yes"], tmpdir)
        assert result.returncode == 2, (bad, result.returncode)
    print("PASS invalid IDs to delete exit 2")

    result = run(["add", "--name", "Eraser", "--price", "0.75", "--quantity", "3"], tmpdir)
    new_id = json.loads(result.stdout)["id"]
    assert new_id == 3, new_id
    print("PASS after deleting ID 2, the next add gets ID 3 — IDs are never reused")

    result = run(["delete", "1", "--yes"], tmpdir)
    assert result.returncode == 0
    result = run(["delete", "3", "--yes"], tmpdir)
    assert result.returncode == 0
    result = run(["list"], tmpdir)
    assert result.stdout.strip() == "[]"
    print("PASS deleting every product leaves list printing []")

with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["delete", "1", "--yes"], tmpdir)
    assert result.returncode == 1 and "1" in result.stderr
    assert not os.path.exists(os.path.join(tmpdir, "products.json"))
    print("PASS delete with no data file reports missing ID 1 and creates nothing")

    data_file = setup(tmpdir)
    with open(data_file, "w", encoding="utf-8") as handle:
        handle.write("{oops")
    before_broken = read_bytes(data_file)
    result = run(["delete", "1", "--yes"], tmpdir)
    assert result.returncode == 1 and result.stdout == ""
    assert read_bytes(data_file) == before_broken
    print("PASS delete against malformed file exits 1 and leaves it unchanged")

print("ALL STEP 7 TESTS PASSED")
