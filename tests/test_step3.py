"""Automated checks for step 3 (input validation helpers) of products.py."""

import sys

sys.path.insert(0, "/Users/nikitaxu/Viber/ISBA2438")
import products


def check_ok(label, function, value, expected):
    result = function(value)
    assert result == expected, f"{label}: got {result!r}, expected {expected!r}"
    print(f"PASS {label}: {value!r} -> {result!r}")


def check_rejected(label, function, value):
    try:
        function(value)
    except products.ToolError as error:
        assert error.exit_code == 2, f"{label}: exit code {error.exit_code}, expected 2"
        print(f"PASS (exit 2) {label}: {value!r} -> {error}")
        return
    raise AssertionError(f"{label}: expected ToolError for {value!r}")


print("name:")
check_ok("name trims", products.parse_name, "  Notebook  ", "Notebook")
check_ok("name inner spaces kept", products.parse_name, " Blue  pen ", "Blue  pen")
check_rejected("name all whitespace", products.parse_name, "   ")
check_rejected("name empty", products.parse_name, "")

print("\nprice:")
check_ok("price zero", products.parse_price, "0", "0.00")
check_ok("price one decimal", products.parse_price, "4.5", "4.50")
check_ok("price two decimals", products.parse_price, "4.50", "4.50")
check_ok("price whole digits", products.parse_price, "12", "12.00")
check_ok("price cents", products.parse_price, "0.99", "0.99")
check_ok("price leading zeros", products.parse_price, "007", "7.00")
check_ok("price big", products.parse_price, "123456789012345", "123456789012345.00")
for bad in ["+4", "-4", "$4", "4.", ".5", "4.500", "1e2", "4,50", "", " 4.5", "4.5 ", "-0"]:
    check_rejected("price invalid", products.parse_price, bad)

print("\nquantity:")
check_ok("quantity zero", products.parse_quantity, "0", 0)
check_ok("quantity ten", products.parse_quantity, "10", 10)
check_ok("quantity leading zeros", products.parse_quantity, "007", 7)
for bad in ["-1", "1.5", "1e2", "+5", "5 ", "abc", "", "٥"]:
    check_rejected("quantity invalid", products.parse_quantity, bad)

print("\nid:")
check_ok("id one", products.parse_id, "1", 1)
check_ok("id big", products.parse_id, "123", 123)
for bad in ["0", "-1", "abc", "1.5", "", "1 ", "٥"]:
    check_rejected("id invalid", products.parse_id, bad)

print("\nALL STEP 3 TESTS PASSED")
