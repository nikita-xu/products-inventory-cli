"""Verifies error handling for bad data files: empty, malformed JSON, invalid
UTF-8 bytes, and a UTF-8 BOM — every case must exit 1 with a concise stderr
message, no traceback, empty stdout, and the file left byte-identical."""

import os
import subprocess
import sys
import tempfile

WORKSPACE = "/Users/nikitaxu/Viber/ISBA2438"

CASES = {
    "empty file": b"",
    "whitespace only": b"  \n\t ",
    "malformed JSON": b'{"next_id": 2, "products": [',
    "truncated product": b'{"next_id": 2, "products": [{"id": 1}',
    "invalid UTF-8 first byte": b'\xff\xfe{"next_id": 2}',
    "invalid UTF-8 inside a string": b'{"name": "\x80"}',
    "UTF-8 BOM prefix": b'\xef\xbb\xbf{"next_id": 2, "products": []}',
}

with tempfile.TemporaryDirectory() as tmpdir:
    data_file = os.path.join(tmpdir, "products.json")
    for label, raw_bytes in CASES.items():
        with open(data_file, "wb") as handle:
            handle.write(raw_bytes)
        before = open(data_file, "rb").read()
        for command in (
            ["list"],
            ["get", "1"],
            ["add", "--name", "X", "--price", "1", "--quantity", "1"],
        ):
            result = subprocess.run(
                [sys.executable, os.path.join(WORKSPACE, "products.py")] + command,
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            assert result.returncode == 1, (label, command, result.returncode, result.stderr)
            assert result.stdout == "", (label, command, result.stdout)
            assert result.stderr.strip() != "", (label, command)
            assert "Traceback" not in result.stderr, (label, command, result.stderr)
            assert open(data_file, "rb").read() == before, label
        print(f"PASS {label}: exit 1, stderr only, no traceback, file byte-identical")

print("BAD DATA FILES: ALL CASES HANDLED")
