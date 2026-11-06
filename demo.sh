#!/bin/bash
# Assignment 1 dress rehearsal — the exact sequence from the handout, plus
# error cases, the custom low-stock feature, and --file persistence.
# Run from the folder containing products.py:   bash demo.sh
set -u

printf 'Resetting to a missing products.json (the handout starts from no file)\n'
rm -f products.json demo.json

r() { printf '\n$ %s\n' "$*"; "$@"; printf '[exit %s]\n' "$?"; }

# Required success sequence
r python3 products.py --help
r python3 products.py add --name "Notebook" --price 4.5 --quantity 10
r python3 products.py add --name "Pencil" --price 1.25 --quantity 5
r python3 products.py list
r python3 products.py get 1
r python3 products.py update 1 --quantity 12
r python3 products.py delete 2 --yes
r python3 products.py list

printf '\n--- products.json ---\n'
cat products.json

# Persistence: a later invocation reads the saved data
r python3 products.py get 1

# Error behavior (file must stay unchanged)
BEFORE=$(shasum -a 256 products.json | cut -d' ' -f1)
r python3 products.py get 99
r python3 products.py add --name "Bad" --price 4.5.5 --quantity 1
r python3 products.py delete 1
AFTER=$(shasum -a 256 products.json | cut -d' ' -f1)
[ "$BEFORE" = "$AFTER" ] && printf '\n[ok] failed commands left products.json byte-identical\n'

# --file with a separate data file
r python3 products.py --file demo.json add --name "Sticky notes" --price 2.5 --quantity 4
r python3 products.py --file demo.json list
r python3 products.py list

# Custom feature: low-stock report
r python3 products.py --file demo.json low-stock --threshold 4
r python3 products.py low-stock --threshold 20
r python3 products.py low-stock --threshold 5
r python3 products.py low-stock --threshold=-3
