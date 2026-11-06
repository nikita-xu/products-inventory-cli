"""Verifies the handout's ID and next_id lifecycle rules end-to-end."""

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


def next_id(tmpdir):
    path = os.path.join(tmpdir, "products.json")
    return json.loads(open(path, encoding="utf-8").read())["next_id"]


with tempfile.TemporaryDirectory() as tmpdir:
    result = run(["add", "--name", "A", "--price", "1", "--quantity", "1"], tmpdir)
    assert json.loads(result.stdout)["id"] == 1
    print("PASS IDs start at 1 on a fresh store")

    ids = [1]
    for name in ["B", "C"]:
        result = run(["add", "--name", name, "--price", "2", "--quantity", "2"], tmpdir)
        ids.append(json.loads(result.stdout)["id"])
    assert ids == [1, 2, 3] and next_id(tmpdir) == 4
    print("PASS each successful add assigns next_id and increments it (1, 2, 3)")

    result = run(["update", "1", "--name", "Renamed", "--price", "9", "--quantity", "9"], tmpdir)
    updated = json.loads(result.stdout)
    assert updated["id"] == 1 and next_id(tmpdir) == 4
    print("PASS update keeps the ID and does not change next_id")

    result = run(["delete", "2", "--yes"], tmpdir)
    assert result.returncode == 0 and next_id(tmpdir) == 4
    print("PASS delete does not change next_id")

    result = run(["add", "--name", "D", "--price", "3", "--quantity", "3"], tmpdir)
    new_id = json.loads(result.stdout)["id"]
    assert new_id == 4
    print("PASS after deleting ID 2, the next add gets ID 4 — deleted IDs are never reused")

    result = run(["delete", "3", "--yes"], tmpdir)
    result = run(["delete", "4", "--yes"], tmpdir)
    assert next_id(tmpdir) == 5
    result = run(["add", "--name", "E", "--price", "4", "--quantity", "4"], tmpdir)
    assert json.loads(result.stdout)["id"] == 5
    print("PASS deleting the highest ID (3, then 4) still never causes reuse (next: 5)")

    result = run(["delete", "1", "--yes"], tmpdir)
    result = run(["delete", "5", "--yes"], tmpdir)
    assert next_id(tmpdir) == 6
    result = run(["add", "--name", "F", "--price", "5", "--quantity", "5"], tmpdir)
    assert json.loads(result.stdout)["id"] == 6
    print("PASS even with zero products left, next_id continues (6) — nothing resets")

    crafted = os.path.join(tmpdir, "products.json")
    with open(crafted, "w", encoding="utf-8") as handle:
        handle.write('{"next_id": 2, "products": [{"id": 2, "name": "x", "price": "1.00", "quantity": 1}]}')
    result = run(["list"], tmpdir)
    assert result.returncode == 1 and result.stdout == ""
    print("PASS a file where next_id is not above every product ID is rejected (exit 1)")

print("ID LIFECYCLE: ALL HANDOUT RULES VERIFIED")
