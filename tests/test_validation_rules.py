"""Verifies the handout's field rules (lines 44-56) end-to-end through the CLI:
name trimming/duplicates, price shapes and storage, quantity rules, and the
same rules enforced on data read from an existing file."""

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


def add(name, price, quantity, cwd):
    return run(["add", "--name", name, "--price", price, "--quantity", quantity], cwd)


with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")

    result = add("  Notebook  ", "4.5", "10", tmpdir)
    assert json.loads(result.stdout)["name"] == "Notebook"
    print("PASS name: outer whitespace trimmed before storing")

    result = add("  Blue  pen ", "4.50", "1", tmpdir)
    assert json.loads(result.stdout)["name"] == "Blue  pen"
    print("PASS name: inner spacing preserved exactly")

    result = add("Notebook", "5", "1", tmpdir)
    assert result.returncode == 0 and json.loads(result.stdout)["id"] == 3
    print("PASS name: duplicate names are allowed (second Notebook got ID 3)")

    for text, stored in [("0", "0.00"), ("4.5", "4.50"), ("4.50", "4.50"), ("120", "120.00")]:
        result = add("P", text, "1", tmpdir)
        assert result.returncode == 0 and json.loads(result.stdout)["price"] == stored, (text, result)
        print(f"PASS price: '{text}' accepted and stored as '{stored}'")

    result = add("P", "0.99", "0", tmpdir)
    assert result.returncode == 0 and json.loads(result.stdout)["quantity"] == 0
    print("PASS quantity: zero is accepted")

    before = open(data_file, "rb").read()
    rejects = [
        ["add", "--name", "", "--price", "1", "--quantity", "1"],
        ["add", "--name", "   ", "--price", "1", "--quantity", "1"],
        ["add", "--name", "X", "--price", "+4.50", "--quantity", "1"],
        ["add", "--name", "X", "--price", "-4.50", "--quantity", "1"],
        ["add", "--name", "X", "--price", "$4.50", "--quantity", "1"],
        ["add", "--name", "X", "--price", "4.5.5", "--quantity", "1"],
        ["add", "--name", "X", "--price", "4.500", "--quantity", "1"],
        ["add", "--name", "X", "--price", "1e2", "--quantity", "1"],
        ["add", "--name", "X", "--price", ".5", "--quantity", "1"],
        ["add", "--name", "X", "--price", "4.", "--quantity", "1"],
        ["add", "--name", "X", "--price", "4,50", "--quantity", "1"],
        ["add", "--name", "X", "--price", "1", "--quantity", "-1"],
        ["add", "--name", "X", "--price", "1", "--quantity", "1.5"],
        ["add", "--name", "X", "--price", "1", "--quantity", "1e2"],
        ["add", "--name", "X", "--price", "1", "--quantity", "abc"],
        ["add", "--name", "X", "--price", "1", "--quantity", "+5"],
        ["update", "1", "--price", "4.5.5"],
        ["update", "1", "--name", "   "],
        ["update", "1", "--quantity", "-2"],
    ]
    for case in rejects:
        result = run(case, tmpdir)
        assert result.returncode == 2, (case, result.returncode, result.stderr)
        assert result.stdout == "", case
        assert result.stderr.strip() != "", case
    assert open(data_file, "rb").read() == before
    print(f"PASS all {len(rejects)} prohibited shapes rejected (exit 2, stderr only, file byte-identical)")

with tempfile.TemporaryDirectory() as tmpdir:
    crafted = os.path.join(tmpdir, "products.json")
    bad_stored = {
        'price with one decimal': '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": "4.5", "quantity": 1}]}',
        'price as a number': '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": 4.5, "quantity": 1}]}',
        'negative quantity': '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": "4.50", "quantity": -1}]}',
        'blank name': '{"next_id": 2, "products": [{"id": 1, "name": "  ", "price": "4.50", "quantity": 1}]}',
        'boolean quantity': '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": "4.50", "quantity": true}]}',
    }
    for label, text in bad_stored.items():
        with open(crafted, "w", encoding="utf-8") as handle:
            handle.write(text)
        before = open(crafted, "rb").read()
        result = run(["list"], tmpdir)
        assert result.returncode == 1 and result.stdout == "", (label, result)
        assert open(crafted, "rb").read() == before
        print(f"PASS stored data: {label} rejected at load (exit 1, file unchanged)")

print("FIELD VALIDATION: ALL HANDOUT RULES VERIFIED")
