"""Automated checks for step 2 (storage helpers) of products.py."""

import json
import os
import sys
import tempfile

sys.path.insert(0, "/Users/nikitaxu/Viber/ISBA2438")
import products


def expect_error(label, function, *args):
    try:
        function(*args)
    except products.ToolError as error:
        print(f"PASS (exit {error.exit_code}) {label}: {error}")
        return
    raise AssertionError(f"expected ToolError for: {label}")


def write(tmpdir, text, name="bad.json"):
    path = os.path.join(tmpdir, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


with tempfile.TemporaryDirectory() as tmpdir:
    missing = os.path.join(tmpdir, "nope.json")
    store = products.load_store(missing)
    assert store == {"next_id": 1, "products": []}, store
    assert not os.path.exists(missing)
    print("PASS missing file -> empty store, and file was not created")

    good = {
        "next_id": 3,
        "products": [
            {"id": 1, "name": "Café mug", "price": "4.50", "quantity": 10},
            {"id": 2, "name": "Pencil", "price": "1.25", "quantity": 0},
        ],
    }
    saved_path = os.path.join(tmpdir, "good.json")
    products.save_store(saved_path, good)
    assert products.load_store(saved_path) == good
    with open(saved_path, "r", encoding="utf-8") as handle:
        text = handle.read()
    assert '"4.50"' in text and "Café mug" in text and '"next_id": 3' in text
    print("PASS save/load round trip keeps two-decimal prices and UTF-8 names")

    bad_dir = os.path.join(tmpdir, "no_such_dir", "x.json")
    expect_error("write into missing directory", products.save_store, bad_dir, good)
    assert not os.path.exists(os.path.dirname(bad_dir))
    print("PASS missing parent directory was not created")

    malformed = write(tmpdir, '{"next_id": 2, "products": [', name="malformed.json")
    before = open(malformed, "rb").read()
    expect_error("malformed JSON", products.load_store, malformed)
    assert open(malformed, "rb").read() == before
    print("PASS malformed file left byte-for-byte unchanged")

    expect_error("empty file", products.load_store, write(tmpdir, "   \n", name="empty.json"))

    bad_stores = {
        "store is not an object": "[]",
        "missing next_id": '{"products": []}',
        "next_id is zero": '{"next_id": 0, "products": []}',
        "next_id is true": '{"next_id": true, "products": []}',
        "products is an object": '{"next_id": 2, "products": {}}',
        "product is not an object": '{"next_id": 2, "products": [1]}',
        "id is zero": '{"next_id": 2, "products": [{"id": 0, "name": "x", "price": "1.00", "quantity": 1}]}',
        "id is text": '{"next_id": 2, "products": [{"id": "1", "name": "x", "price": "1.00", "quantity": 1}]}',
        "id is true": '{"next_id": 2, "products": [{"id": true, "name": "x", "price": "1.00", "quantity": 1}]}',
        "duplicate ids": '{"next_id": 3, "products": [{"id": 1, "name": "x", "price": "1.00", "quantity": 1}, {"id": 1, "name": "y", "price": "2.00", "quantity": 2}]}',
        "next_id not above ids": '{"next_id": 1, "products": [{"id": 1, "name": "x", "price": "1.00", "quantity": 1}]}',
        "name is blank": '{"next_id": 2, "products": [{"id": 1, "name": "   ", "price": "1.00", "quantity": 1}]}',
        "price has one decimal": '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": "1.5", "quantity": 1}]}',
        "price is a number": '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": 1.5, "quantity": 1}]}',
        "quantity is negative": '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": "1.00", "quantity": -1}]}',
        "quantity is text": '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": "1.00", "quantity": "3"}]}',
        "quantity missing": '{"next_id": 2, "products": [{"id": 1, "name": "x", "price": "1.00"}]}',
    }
    for label, text in bad_stores.items():
        expect_error(label, products.load_store, write(tmpdir, text))
    print(f"PASS all {len(bad_stores)} schema violations rejected with exit code 1")

print("ALL STEP 2 TESTS PASSED")
