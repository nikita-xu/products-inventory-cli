"""Verifies the exact required command sequence from the assignment handout,
starting from a missing products.json, including the stated expected results."""

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


NOTEBOOK = {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 10}
PENCIL = {"id": 2, "name": "Pencil", "price": "1.25", "quantity": 5}

with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")

    result = run(["--help"], tmpdir)
    assert result.returncode == 0, result.stderr
    for name in ["add", "list", "get", "update", "delete", "low-stock"]:
        assert name in result.stdout, f"missing {name} in help"
    assert not os.path.exists(data_file)
    print("PASS 1: --help exits 0, lists all six commands, file not created")

    result = run(["add", "--name", "Notebook", "--price", "4.5", "--quantity", "10"], tmpdir)
    assert result.returncode == 0 and json.loads(result.stdout) == NOTEBOOK, result
    assert json.loads(open(data_file, encoding="utf-8").read())["next_id"] == 2
    print("PASS 2: first add assigns ID 1, prints the product, saves next_id 2")

    result = run(["add", "--name", "Pencil", "--price", "1.25", "--quantity", "5"], tmpdir)
    assert result.returncode == 0 and json.loads(result.stdout) == PENCIL, result
    assert json.loads(open(data_file, encoding="utf-8").read())["next_id"] == 3
    print("PASS 3: second add assigns ID 2, saves next_id 3")

    result = run(["list"], tmpdir)
    assert json.loads(result.stdout) == [NOTEBOOK, PENCIL], result.stdout
    print("PASS 4: list prints both products sorted by ID")

    result = run(["get", "1"], tmpdir)
    assert json.loads(result.stdout) == NOTEBOOK, result.stdout
    print("PASS 5: get 1 prints exactly the ID-1 product")

    result = run(["update", "1", "--quantity", "12"], tmpdir)
    updated = json.loads(result.stdout)
    assert updated == {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 12}, updated
    print("PASS 6: update changes only quantity; name, price, ID preserved")

    result = run(["delete", "2", "--yes"], tmpdir)
    assert json.loads(result.stdout) == {"deleted_id": 2}, result.stdout
    print("PASS 7: delete 2 --yes prints the deleted ID")

    result = run(["list"], tmpdir)
    assert json.loads(result.stdout) == [
        {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 12}
    ], result.stdout
    print("PASS 8: final list contains only Notebook with price 4.50 and quantity 12")

    on_disk = json.loads(open(data_file, encoding="utf-8").read())
    assert on_disk == {
        "next_id": 3,
        "products": [{"id": 1, "name": "Notebook", "price": "4.50", "quantity": 12}],
    }, on_disk
    assert isinstance(on_disk["products"][0]["price"], str)
    print("PASS 9: saved file is next_id 3 with Notebook; price stored as a string")

    result = run(["get", "1"], tmpdir)
    assert result.returncode == 0 and json.loads(result.stdout)["quantity"] == 12
    print("PASS 10: a later invocation reads the saved data (quantity 12)")

print("REQUIRED SEQUENCE: ALL EXPECTATIONS MET")
