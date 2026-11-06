"""Verifies exact-flag enforcement and stored-name canonical-form checks:
abbreviated flags are rejected, exact flags (including --name=value) work,
names supplied to add/update are still trimmed, and stored names must be
trimmed exactly as the tool itself would store them."""

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


with tempfile.TemporaryDirectory() as tmpdir:
    abbreviations = [
        ["add", "--na", "X", "--price", "1", "--quantity", "1"],
        ["add", "--name", "X", "--price", "1", "--quant", "1"],
        ["--f", "demo.json", "list"],
        ["low-stock", "--thr", "5"],
        ["delete", "1", "--y"],
    ]
    for args in abbreviations:
        result = run(args, tmpdir)
        assert result.returncode == 2, (args, result.returncode, result.stderr)
        assert result.stdout == ""
        assert "Traceback" not in result.stderr
    print(f"PASS all {len(abbreviations)} abbreviated flags rejected with exit 2, no traceback")

    result = run(["add", "--name=X", "--price=1", "--quantity=1"], tmpdir)
    assert result.returncode == 0 and json.loads(result.stdout)["name"] == "X", result
    print("PASS exact flags still work, including --name=value syntax")

    result = run(["add", "--name", "  Padded  ", "--price", "2", "--quantity", "3"], tmpdir)
    assert json.loads(result.stdout)["name"] == "Padded"
    print("PASS names supplied through add are still trimmed before storing")

    result = run(["update", "1", "--name", "  Renamed  "], tmpdir)
    assert json.loads(result.stdout)["name"] == "Renamed"
    print("PASS names supplied through update are still trimmed before storing")

    data_file = os.path.join(tmpdir, "products.json")
    good = {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 1}
    stored_cases = {
        "clean name (control)": "Notebook",
        "leading space": " Notebook",
        "trailing space": "Notebook ",
        "tab padding": "\tPencil\t",
        "trailing newline": "Notebook\n",
    }
    for label, name in stored_cases.items():
        product = dict(good, name=name)
        with open(data_file, "w", encoding="utf-8") as handle:
            json.dump({"next_id": 2, "products": [product]}, handle)
        before = open(data_file, "rb").read()
        for command in (
            ["list"],
            ["get", "1"],
            ["low-stock", "--threshold", "5"],
            ["update", "1", "--quantity", "2"],
        ):
            result = run(command, tmpdir)
            if label == "clean name (control)":
                assert result.returncode == 0, (label, command, result.stderr)
            else:
                assert result.returncode == 1, (label, command, result.returncode, result.stderr)
                assert result.stdout == "", (label, command)
                assert "Traceback" not in result.stderr, (label, command, result.stderr)
                assert open(data_file, "rb").read() == before, (label, command)
        if label == "clean name (control)":
            print("PASS stored clean name accepted by every command (control)")
        else:
            print(f"PASS stored {label}: exit 1, stderr only, no traceback, file byte-identical")

print("EXACT FLAGS AND STORED-NAME RULES: ALL VERIFIED")
