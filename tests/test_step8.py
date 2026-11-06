"""Automated checks for step 8 (low-stock, the custom feature) of products.py."""

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


def product(product_id, quantity):
    return {"id": product_id, "name": f"P{product_id}", "price": "1.00", "quantity": quantity}


SEEDED = {
    "next_id": 5,
    "products": [
        product(4, 7),
        product(1, 0),
        product(3, 5),
        product(2, 3),
    ],
}


def seed(tmpdir, name="products.json", store=SEEDED):
    path = os.path.join(tmpdir, name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(store, handle)
    return path


with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["low-stock", "--threshold", "5"], tmpdir)
    assert result.returncode == 0 and result.stdout.strip() == "[]", result
    assert not os.path.exists(os.path.join(tmpdir, "products.json"))
    print("PASS low-stock with no data file prints [] and creates nothing")

    data_file = seed(tmpdir)
    before = read_bytes(data_file)

    result = run(["low-stock", "--threshold", "5"], tmpdir)
    assert result.returncode == 0, result.stderr
    ids = [p["id"] for p in json.loads(result.stdout)]
    assert ids == [1, 2, 3], result.stdout
    print("PASS threshold 5 returns quantities 0, 3, 5 (<=), sorted by ID")

    result = run(["low-stock", "--threshold", "0"], tmpdir)
    assert [p["id"] for p in json.loads(result.stdout)] == [1]
    print("PASS threshold 0 returns only the quantity-0 product")

    result = run(["low-stock", "--threshold", "1000000"], tmpdir)
    assert [p["id"] for p in json.loads(result.stdout)] == [1, 2, 3, 4]
    print("PASS a huge threshold returns every product")

    assert read_bytes(data_file) == before
    print("PASS a successful low-stock leaves the file byte-identical")

    bad_thresholds = ["-1", "abc", "1.5", "", "+2", "3 "]
    for bad in bad_thresholds:
        result = run(["low-stock", "--threshold", bad], tmpdir)
        assert result.returncode == 2, (bad, result.returncode, result.stderr)
        assert result.stdout == ""
    result = run(["low-stock"], tmpdir)
    assert result.returncode == 2 and result.stdout == ""
    assert read_bytes(data_file) == before
    print(f"PASS {len(bad_thresholds) + 1} invalid threshold invocations exit 2, file unchanged")

    result = run(["--help"], tmpdir)
    assert "low-stock" in result.stdout and result.returncode == 0
    print("PASS low-stock appears in --help")

    other = seed(tmpdir, name="demo.json")
    before_other = read_bytes(other)
    result = run(["--file", "demo.json", "low-stock", "--threshold", "3"], tmpdir)
    assert result.returncode == 0 and [p["id"] for p in json.loads(result.stdout)] == [1, 2]
    assert read_bytes(other) == before_other
    print("PASS --file demo.json reads the other store and leaves it unchanged")

    with open(data_file, "w", encoding="utf-8") as handle:
        handle.write("{oops")
    before_broken = read_bytes(data_file)
    result = run(["low-stock", "--threshold", "5"], tmpdir)
    assert result.returncode == 1 and result.stdout == ""
    assert read_bytes(data_file) == before_broken
    print("PASS low-stock against malformed file exits 1 and leaves it unchanged")

print("ALL STEP 8 TESTS PASSED")
