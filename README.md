# products.py — a tiny store inventory CLI

A Python 3 command-line tool for managing a small store's product inventory.
Products live in a local JSON file, so every command reads what the last command
saved. Built for ISBA 2438 (AI Assisted Software Development), Assignment 1.

Requires **Python 3 only** — no third-party packages. On Windows, `py -3` works
in place of `python3`.

## Quick start

```bash
python3 products.py add --name "Notebook" --price 4.5 --quantity 10
python3 products.py list
python3 products.py get 1
```

The first successful `add` creates `products.json` in the current directory.
Read-only commands (`list`, `get`, `low-stock`) never create or rewrite it.

## How to invoke

```bash
python3 products.py [--file PATH] COMMAND [OPTIONS]
```

`--file PATH` selects the data file and must come **before** the command
(default: `products.json`). Relative paths resolve from your current directory.

## Commands

| Command | What it does |
|---|---|
| `add --name NAME --price PRICE --quantity QTY` | Create one product; the tool assigns the ID and prints it as JSON |
| `list` | Print all products as a JSON array sorted by ID (`[]` when empty) |
| `get ID` | Print one product as a JSON object |
| `update ID [--name N] [--price P] [--quantity Q]` | Change only the supplied fields (at least one required) |
| `delete ID --yes` | Remove one product (`--yes` confirms); prints `{"deleted_id": ID}` |
| `low-stock --threshold N` | *Custom feature* — see below |

Every command also supports `--help`, which never touches the data file.

## Data rules

- **id** — positive integer, assigned automatically starting at 1, never reused
- **name** — trimmed of surrounding whitespace, at least one character; duplicates allowed
- **price** — nonnegative, at most two decimals; stored as a string with exactly
  two decimals (`4.5` becomes `"4.50"`)
- **quantity** — nonnegative whole number (zero is allowed)

## Storage

Data is UTF-8 JSON with this shape:

```json
{
  "next_id": 2,
  "products": [
    {"id": 1, "name": "Notebook", "price": "4.50", "quantity": 10}
  ]
}
```

Saves are atomic: each write goes to a temporary file in the same directory that
is swapped into place only after it is complete, so a failed save can never
destroy the existing store.

## Errors and exit codes

Failures print one concise explanation to standard error (never a Python
traceback, never JSON on stdout) and leave the data file unchanged.

| Exit code | Meaning |
|---|---|
| `0` | Success, including an empty result or `--help` |
| `1` | Product ID not found, invalid stored data, or file read/write failure |
| `2` | Bad syntax, missing arguments, or invalid input values |

## Custom feature: `low-stock`

```bash
python3 products.py low-stock --threshold N
```

Prints a JSON array of every product whose quantity is **less than or equal to**
`N`, sorted by ID. `N` must be a nonnegative whole number. Returns `[]` when
nothing matches, supports `--file`, and never modifies the data file.

**Who it helps:** a shop owner doing a quick restock check — before opening or
before placing a supplier order, one command shows everything that is running
low without reading the whole list by eye.

**Examples:**

```bash
$ python3 products.py add --name "Mug" --price 3.5 --quantity 5
{"id": 1, "name": "Mug", "price": "3.50", "quantity": 5}
$ python3 products.py add --name "Notebook" --price 4.5 --quantity 12
{"id": 2, "name": "Notebook", "price": "4.50", "quantity": 12}

$ python3 products.py low-stock --threshold 5
[{"id": 1, "name": "Mug", "price": "3.50", "quantity": 5}]

$ python3 products.py low-stock --threshold 20
[{"id": 1, "name": "Mug", "price": "3.50", "quantity": 5},
 {"id": 2, "name": "Notebook", "price": "4.50", "quantity": 12}]

$ python3 products.py low-stock --threshold 0
[]

$ python3 products.py low-stock --threshold=-3
products.py: error: quantity '-3' is invalid: use a whole number of 0 or more
```

The threshold is *at or below*, so quantity 5 matches threshold 5 exactly. An
empty result is still a success (exit 0); an invalid threshold is rejected
before the data file is opened (exit 2).

## Tests

```bash
python3 tests/test_demo_sequence.py
```

`tests/` contains focused suites covering the required command sequence, field
validation, ID lifecycle, file behavior, exit codes, corrupt data files,
atomic writes, exact-flag handling, and long numbers. Run any file with
`python3 tests/<name>.py` — each prints one `PASS` line per check.

## Development

Built incrementally with a coding agent under the course's AI-assisted workflow
(incremental prompts, review, and testing after every step). All code was
reviewed, tested, and explained by the repository owner — see the per-suite
tests for the executable form of that review.

## Repository layout

```
products.py      the tool (single file, standard library only)
tests/           automated checks, one suite per requirement area
demo.sh          replays the full demonstration sequence from a clean start
playground.py    optional practice helper (not part of the tool)
```
