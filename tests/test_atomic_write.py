"""Verifies save_store is atomic and safe under interference:
- a write that fails midway leaves the original file byte-identical
- only the temp file created by this operation is cleaned up, never user data
- cleanup failures never mask the original error
- a pre-existing directory named products.json.tmp does not break saving
- replacement failures and encoding failures exit cleanly
This is the regression test for the torn-write and temp-file problems
(handout: failed commands must not alter the data file, no tracebacks)."""

import json
import os
import subprocess
import sys
import tempfile

WORKSPACE = "/Users/nikitaxu/Viber/ISBA2438"
sys.path.insert(0, WORKSPACE)
import products

GOOD_STORE = {
    "next_id": 3,
    "products": [
        {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 12},
        {"id": 2, "name": "Pencil", "price": "1.25", "quantity": 5},
    ],
}

real_dump = json.dump
real_dumps = json.dumps
real_remove = os.remove


def failing_dump(obj, handle, **kwargs):
    text = real_dumps(obj, indent=2, ensure_ascii=False)
    handle.write(text[: len(text) // 2])
    handle.flush()
    raise OSError(28, "No space left on device")


def expect_tool_error(action, label):
    try:
        action()
        raise AssertionError(f"{label}: expected ToolError")
    except products.ToolError as error:
        assert "cannot write data file" in str(error), (label, error)
        print(f"PASS {label}: {error}")
        return error


with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")
    with open(data_file, "w", encoding="utf-8") as handle:
        json.dump(GOOD_STORE, handle, indent=2, ensure_ascii=False)
    before = open(data_file, "rb").read()

    products.json.dump = failing_dump
    try:
        expect_tool_error(lambda: products.save_store(data_file, GOOD_STORE), "mid-write failure reported")
    finally:
        json.dump = real_dump

    assert open(data_file, "rb").read() == before, "torn write damaged the original file!"
    print(f"PASS original file byte-identical after the failed save ({len(before)} bytes)")

    assert os.listdir(tmpdir) == ["products.json"], os.listdir(tmpdir)
    print("PASS no temp file of any name left behind")

    assert products.load_store(data_file) == GOOD_STORE
    print("PASS the store still loads with both products and next_id 3")

with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")
    blocker = os.path.join(tmpdir, "products.json.tmp")
    os.mkdir(blocker)
    products.save_store(data_file, GOOD_STORE)
    assert products.load_store(data_file) == GOOD_STORE
    assert os.path.isdir(blocker), "the pre-existing directory was removed!"
    print("PASS a directory named products.json.tmp does not break saving and is never touched")

with tempfile.TemporaryDirectory() as tmpdir:
    target_is_directory = os.path.join(tmpdir, "products.json")
    os.mkdir(target_is_directory)
    expect_tool_error(lambda: products.save_store(target_is_directory, GOOD_STORE), "replacement failure reported")
    assert os.path.isdir(target_is_directory), "the directory was altered!"
    assert os.listdir(tmpdir) == ["products.json"], os.listdir(tmpdir)
    print("PASS failed replacement leaves the directory in place and cleans the temp file")

with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")
    with open(data_file, "w", encoding="utf-8") as handle:
        json.dump(GOOD_STORE, handle, indent=2, ensure_ascii=False)
    before = open(data_file, "rb").read()
    products.json.dump = failing_dump
    products.os.remove = lambda path: (_ for _ in ()).throw(OSError(1, "simulated cleanup failure"))
    try:
        expect_tool_error(lambda: products.save_store(data_file, GOOD_STORE), "cleanup failure does not mask the write error")
    finally:
        products.os.remove = real_remove
        json.dump = real_dump
    assert open(data_file, "rb").read() == before
    print("PASS the original error is raised even when cleanup itself fails")

with tempfile.TemporaryDirectory() as tmpdir:
    new_file = os.path.join(tmpdir, "products.json")
    products.json.dump = failing_dump
    try:
        expect_tool_error(lambda: products.save_store(new_file, GOOD_STORE), "failed first save reported")
    finally:
        json.dump = real_dump
    assert os.listdir(tmpdir) == [], os.listdir(tmpdir)
    print("PASS a failed first save creates neither the data file nor a temp file")

with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")
    with open(data_file, "w", encoding="utf-8") as handle:
        handle.write('{"next_id": 2, "products": [{"id": 1, "name": "\\ud800bad", "price": "1.00", "quantity": 1}]}')
    before = open(data_file, "rb").read()
    result = subprocess.run(
        [sys.executable, os.path.join(WORKSPACE, "products.py"), "update", "1", "--quantity", "2"],
        capture_output=True, text=True, cwd=tmpdir,
    )
    assert result.returncode == 1 and result.stdout == "", (result.returncode, result.stderr)
    assert "Traceback" not in result.stderr
    assert open(data_file, "rb").read() == before
    print("PASS unencodable stored name (lone surrogate): exit 1, no traceback, file unchanged")

with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")
    products.save_store(data_file, GOOD_STORE)
    result = subprocess.run(
        [sys.executable, os.path.join(WORKSPACE, "products.py"), "get", "1"],
        capture_output=True, text=True, cwd=tmpdir,
    )
    assert result.returncode == 0 and json.loads(result.stdout)["name"] == "Notebook"
    assert os.listdir(tmpdir) == ["products.json"], os.listdir(tmpdir)
    print("PASS a successful save leaves exactly the data file and the CLI reads it")

print("ATOMIC WRITE: TORN-WRITE AND TEMP-FILE REGRESSIONS VERIFIED")
