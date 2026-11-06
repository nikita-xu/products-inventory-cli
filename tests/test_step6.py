"""Automated checks for step 6 (update) of products.py."""

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

    result = run(["update", "1", "--quantity", "12"], tmpdir)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "id": 1, "name": "Notebook", "price": "4.50", "quantity": 12
    }, result.stdout
    store = json.loads(open(data_file, encoding="utf-8").read())
    assert store["next_id"] == 3 and len(store["products"]) == 2
    print("PASS update 1 --quantity 12 changes only quantity; next_id stays 3")

    result = run(["get", "1"], tmpdir)
    assert json.loads(result.stdout)["quantity"] == 12
    print("PASS a later invocation sees the updated data")

    result = run(["update", "1", "--name", "  New Name  ", "--price", "2"], tmpdir)
    updated = json.loads(result.stdout)
    assert updated["name"] == "New Name" and updated["price"] == "2.00" and updated["quantity"] == 12
    print("PASS multiple fields update together; name trims, price normalizes, quantity preserved")

    before = read_bytes(data_file)
    bad_cases = [
        ["update", "1", "--price", "+4"],
        ["update", "1", "--quantity", "-1"],
        ["update", "1", "--name", "   "],
        ["update", "1", "--name", ""],
        ["update", "1"],
        ["update", "abc", "--quantity", "5"],
        ["update", "0", "--quantity", "5"],
    ]
    for case in bad_cases:
        result = run(case, tmpdir)
        assert result.returncode == 2, (case, result.returncode, result.stderr)
        assert result.stdout == ""
    assert read_bytes(data_file) == before
    print(f"PASS {len(bad_cases)} invalid updates exit 2, stderr only, file byte-identical")

    result = run(["update", "999", "--quantity", "5"], tmpdir)
    assert result.returncode == 1 and result.stdout == "" and "999" in result.stderr
    assert read_bytes(data_file) == before
    print("PASS update of missing ID exits 1, names the ID, file unchanged")

    with open(data_file, "w", encoding="utf-8") as handle:
        handle.write("{oops")
    before_broken = read_bytes(data_file)
    result = run(["update", "1", "--quantity", "5"], tmpdir)
    assert result.returncode == 1 and result.stdout == ""
    assert read_bytes(data_file) == before_broken
    print("PASS update against malformed file exits 1 and leaves it unchanged")

with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["update", "1", "--quantity", "5"], tmpdir)
    assert result.returncode == 1 and "1" in result.stderr
    assert not os.path.exists(os.path.join(tmpdir, "products.json"))
    print("PASS update with no data file reports missing ID 1 and creates nothing")

print("ALL STEP 6 TESTS PASSED")
