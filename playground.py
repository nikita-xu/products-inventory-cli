#!/usr/bin/env python3
"""Interactive playground for products.py — type commands, see output + file state.

Not part of the assignment tool; a helper for exploring and reviewing behavior.

Usage:
    python3 playground.py                (asks for a data file, default products.json)
    python3 playground.py demo.json      (uses demo.json directly)
"""

import json
import shlex
import subprocess
import sys

TOOL = "products.py"


def show_file(data_file):
    print(f"\n--- current {data_file} ---")
    try:
        with open(data_file, "r", encoding="utf-8") as handle:
            content = handle.read().strip()
        print(content if content else "(file exists but is empty)")
    except FileNotFoundError:
        print("(no file yet — read-only commands never create it)")
    except OSError as error:
        print(f"(cannot read file: {error})")
    print()


def run_command(data_file, words):
    result = subprocess.run(
        [sys.executable, TOOL, "--file", data_file] + words,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        try:
            parsed = json.loads(result.stdout)
            print(json.dumps(parsed, indent=2))
        except ValueError:
            print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    print(f"[exit code {result.returncode}]")
    show_file(data_file)


def main():
    data_file = sys.argv[1] if len(sys.argv) > 1 else ""
    if not data_file:
        try:
            data_file = input("Data file to use [products.json]: ").strip()
        except EOFError:
            data_file = ""
        data_file = data_file or "products.json"

    print(f"Playing with {TOOL} --file {data_file}")
    print("Type arguments after the command, e.g.:  add --name Notebook --price 4.5 --quantity 10")
    print("Type 'examples', 'show', or 'quit'.\n")
    while True:
        try:
            line = input(f"{TOOL} $ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("quit", "exit", "q"):
            break
        if line == "show":
            show_file(data_file)
            continue
        if line == "examples":
            print("  add --name Notebook --price 4.5 --quantity 10")
            print("  list")
            print("  get 1")
            print("  update 1 --quantity 12")
            print("  delete 2 --yes")
            print("  low-stock --threshold 5")
            continue
        try:
            words = shlex.split(line)
        except ValueError as error:
            print(f"cannot parse that line: {error}")
            continue
        run_command(data_file, words)


if __name__ == "__main__":
    main()
