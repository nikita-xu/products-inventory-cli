#!/usr/bin/env python3
"""Command-line tool for managing a small store's product inventory."""

import argparse
import json
import os
import re
import sys
import tempfile

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

DEFAULT_FILE = "products.json"
STORED_PRICE_PATTERN = re.compile(r"^[0-9]+\.[0-9]{2}$")
INPUT_PRICE_PATTERN = re.compile(r"^([0-9]+)(\.[0-9]{1,2})?$")
COUNT_PATTERN = re.compile(r"^[0-9]+$")
SCHEMA_MESSAGE = "is inconsistent with the required schema"


class ToolError(Exception):
    def __init__(self, message, exit_code=1):
        super().__init__(message)
        self.exit_code = exit_code


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def load_store(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
    except FileNotFoundError:
        return {"next_id": 1, "products": []}
    except UnicodeDecodeError:
        raise ToolError(f"data file '{path}' is not valid UTF-8")
    except OSError as error:
        raise ToolError(f"cannot read data file '{path}': {error.strerror or error}")
    if content.strip() == "":
        raise ToolError(f"data file '{path}' is empty")
    try:
        store = json.loads(content)
    except ValueError:
        raise ToolError(f"data file '{path}' is not valid JSON")
    check_store_schema(path, store)
    return store


def save_store(path, store):
    directory = os.path.dirname(path) or "."
    temp_path = None
    try:
        descriptor, temp_path = tempfile.mkstemp(
            dir=directory, prefix=f".{os.path.basename(path)}.", suffix=".tmp"
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(store, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temp_path, path)
    except (OSError, ValueError) as error:
        if temp_path is not None:
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise ToolError(
            f"cannot write data file '{path}': {getattr(error, 'strerror', None) or error}"
        )


def check_store_schema(path, store):
    label = f"data file '{path}'"
    if not isinstance(store, dict):
        raise ToolError(f"{label} {SCHEMA_MESSAGE}")
    products = store.get("products")
    next_id = store.get("next_id")
    if not isinstance(products, list):
        raise ToolError(f"{label} {SCHEMA_MESSAGE}: 'products' must be a list")
    if not is_int(next_id) or next_id < 1:
        raise ToolError(f"{label} {SCHEMA_MESSAGE}: 'next_id' must be a positive integer")
    seen_ids = set()
    for product in products:
        check_stored_product(label, product)
        product_id = product["id"]
        if product_id in seen_ids:
            raise ToolError(f"{label} {SCHEMA_MESSAGE}: duplicate product ID {product_id}")
        seen_ids.add(product_id)
        if product_id >= next_id:
            raise ToolError(
                f"{label} {SCHEMA_MESSAGE}: 'next_id' must be greater than every product ID"
            )


def check_stored_product(label, product):
    if not isinstance(product, dict):
        raise ToolError(f"{label} {SCHEMA_MESSAGE}: each product must be an object")
    product_id = product.get("id")
    if not is_int(product_id) or product_id < 1:
        raise ToolError(f"{label} {SCHEMA_MESSAGE}: product 'id' must be a positive integer")
    name = product.get("name")
    if not isinstance(name, str) or name.strip() == "" or name != name.strip():
        raise ToolError(
            f"{label} {SCHEMA_MESSAGE}: product 'name' must be non-empty text "
            "stored without surrounding whitespace"
        )
    price = product.get("price")
    if not isinstance(price, str) or STORED_PRICE_PATTERN.fullmatch(price) is None:
        raise ToolError(
            f"{label} {SCHEMA_MESSAGE}: product 'price' must be a string with two decimals"
        )
    quantity = product.get("quantity")
    if not is_int(quantity) or quantity < 0:
        raise ToolError(
            f"{label} {SCHEMA_MESSAGE}: product 'quantity' must be a nonnegative integer"
        )


def parse_name(value):
    name = value.strip()
    if name == "":
        raise ToolError(
            "name must contain at least one non-whitespace character", exit_code=2
        )
    return name


def parse_price(value):
    match = INPUT_PRICE_PATTERN.fullmatch(value)
    if match is None:
        raise ToolError(
            f"price '{value}' is invalid: use digits with at most two decimals, like 4.50",
            exit_code=2,
        )
    whole = match.group(1)
    fraction = (match.group(2) or "")[1:]
    return f"{int(whole)}.{(fraction + '00')[:2]}"


def parse_quantity(value):
    if COUNT_PATTERN.fullmatch(value) is None:
        raise ToolError(
            f"quantity '{value}' is invalid: use a whole number of 0 or more",
            exit_code=2,
        )
    return int(value)


def parse_id(value):
    if COUNT_PATTERN.fullmatch(value) is None or int(value) < 1:
        raise ToolError(
            f"product ID '{value}' is invalid: use a positive integer", exit_code=2
        )
    return int(value)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="products.py",
        description="Manage a small store's product inventory saved in a JSON file.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--file",
        default=DEFAULT_FILE,
        metavar="PATH",
        help=f"path to the JSON data file (default: {DEFAULT_FILE})",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    add_parser = subparsers.add_parser("add", help="create one product", allow_abbrev=False)
    add_parser.add_argument("--name", required=True, help="product name")
    add_parser.add_argument("--price", required=True, help="price such as 4.5 or 4.50")
    add_parser.add_argument("--quantity", required=True, help="quantity such as 10")

    subparsers.add_parser("list", help="print all products as a JSON array", allow_abbrev=False)

    get_parser = subparsers.add_parser("get", help="print one product as a JSON object", allow_abbrev=False)
    get_parser.add_argument("id", metavar="ID", help="product ID")

    update_parser = subparsers.add_parser("update", help="change supplied fields of one product", allow_abbrev=False)
    update_parser.add_argument("id", metavar="ID", help="product ID")
    update_parser.add_argument("--name", help="new product name")
    update_parser.add_argument("--price", help="new price")
    update_parser.add_argument("--quantity", help="new quantity")

    delete_parser = subparsers.add_parser("delete", help="remove one product", allow_abbrev=False)
    delete_parser.add_argument("id", metavar="ID", help="product ID")
    delete_parser.add_argument("--yes", action="store_true", help="confirm deletion")

    low_stock_parser = subparsers.add_parser(
        "low-stock", help="print products with quantity at or below a threshold", allow_abbrev=False
    )
    low_stock_parser.add_argument(
        "--threshold", required=True, help="maximum quantity to include"
    )

    return parser


def cmd_add(args):
    name = parse_name(args.name)
    price = parse_price(args.price)
    quantity = parse_quantity(args.quantity)
    store = load_store(args.file)
    product = {
        "id": store["next_id"],
        "name": name,
        "price": price,
        "quantity": quantity,
    }
    store["products"].append(product)
    store["next_id"] += 1
    save_store(args.file, store)
    print(json.dumps(product))
    return 0


def cmd_list(args):
    store = load_store(args.file)
    products = sorted(store["products"], key=lambda product: product["id"])
    print(json.dumps(products))
    return 0


def cmd_get(args):
    product_id = parse_id(args.id)
    store = load_store(args.file)
    for product in store["products"]:
        if product["id"] == product_id:
            print(json.dumps(product))
            return 0
    raise ToolError(f"no product with ID {product_id} in '{args.file}'", exit_code=1)


def cmd_update(args):
    product_id = parse_id(args.id)
    name = parse_name(args.name) if args.name is not None else None
    price = parse_price(args.price) if args.price is not None else None
    quantity = parse_quantity(args.quantity) if args.quantity is not None else None
    if name is None and price is None and quantity is None:
        raise ToolError(
            "update requires at least one of --name, --price, --quantity", exit_code=2
        )
    store = load_store(args.file)
    for product in store["products"]:
        if product["id"] == product_id:
            if name is not None:
                product["name"] = name
            if price is not None:
                product["price"] = price
            if quantity is not None:
                product["quantity"] = quantity
            save_store(args.file, store)
            print(json.dumps(product))
            return 0
    raise ToolError(f"no product with ID {product_id} in '{args.file}'", exit_code=1)


def cmd_delete(args):
    product_id = parse_id(args.id)
    if not args.yes:
        raise ToolError("delete requires --yes to confirm", exit_code=2)
    store = load_store(args.file)
    for index, product in enumerate(store["products"]):
        if product["id"] == product_id:
            del store["products"][index]
            save_store(args.file, store)
            print(json.dumps({"deleted_id": product_id}))
            return 0
    raise ToolError(f"no product with ID {product_id} in '{args.file}'", exit_code=1)


def cmd_low_stock(args):
    threshold = parse_quantity(args.threshold)
    store = load_store(args.file)
    matches = [
        product for product in store["products"] if product["quantity"] <= threshold
    ]
    matches.sort(key=lambda product: product["id"])
    print(json.dumps(matches))
    return 0


HANDLERS = {
    "add": cmd_add,
    "list": cmd_list,
    "get": cmd_get,
    "update": cmd_update,
    "delete": cmd_delete,
    "low-stock": cmd_low_stock,
}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return HANDLERS[args.command](args)
    except ToolError as error:
        print(f"products.py: error: {error}", file=sys.stderr)
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
