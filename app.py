#!/usr/bin/env python3
"""Numbeo Cost-of-Living CLI.

Fetches item metadata and city-specific prices from the Numbeo API,
then displays them as a sorted ASCII table in the terminal.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Tuple
from pathlib import Path

# Numbeo REST API endpoints (both require an api_key query parameter).
ITEMS_URL = "https://www.numbeo.com/api/items"
CITY_PRICES_URL = "https://www.numbeo.com/api/city_prices"


def fetch_json(url: str) -> Dict[str, Any]:
    """Perform an HTTP GET request and return the parsed JSON body.

    Raises RuntimeError on any network or decoding failure.
    """
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status} for {url}")
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc


def load_env(path: Path) -> Dict[str, str]:
    """Parse a .env file into a dict, skipping comments and blank lines."""
    if not path.exists():
        return {}
    data: Dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def build_items_index(items: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Build a lookup table mapping item_id to its metadata.

    Each metadata dict contains fields like display_order, category, and name.
    """
    index: Dict[int, Dict[str, Any]] = {}
    for item in items:
        item_id = item.get("item_id")
        if isinstance(item_id, int):
            index[item_id] = item
    return index


def format_money(value: Any, currency: str) -> str:
    """Format a numeric value as a currency string (e.g. '1,234.56 USD').

    Returns '-' when the value is missing or not convertible to a number.
    """
    if value is None:
        return "-"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{num:,.2f} {currency}"


def render_table(rows: List[Tuple[Any, ...]], headers: List[str]) -> str:
    """Render rows and headers as a left-aligned ASCII table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt_row(row: List[Any]) -> str:
        return " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))

    line = "-+-".join("-" * w for w in widths)
    output = [fmt_row(headers), line]
    for row in rows:
        output.append(fmt_row(list(row)))
    return "\n".join(output)


def build_rows(
    prices: List[Dict[str, Any]],
    items_index: Dict[int, Dict[str, Any]],
    currency: str,
) -> List[Tuple[Any, ...]]:
    """Join price entries with item metadata and sort by display_order, then name.

    Each resulting row contains:
    (display_order, category, name, average, lowest, highest, data_points).
    """
    rows = []
    for entry in prices:
        item_id = entry.get("item_id")
        item_meta = items_index.get(item_id, {})
        display_order = item_meta.get("display_order", 10_000)
        category = item_meta.get("category", "-")
        name = item_meta.get("name") or entry.get("item_name", "-")

        rows.append(
            (
                display_order,
                category,
                name,
                format_money(entry.get("average_price"), currency),
                format_money(entry.get("lowest_price"), currency),
                format_money(entry.get("highest_price"), currency),
                entry.get("data_points", "-"),
            )
        )

    rows.sort(key=lambda r: (r[0], r[2]))
    return rows


def main() -> int:
    """Entry point: parse arguments, call the Numbeo API, and print the table."""
    parser = argparse.ArgumentParser(
        description="Fetch Numbeo cost-of-living prices and display them in a table."
    )
    parser.add_argument("--city", required=True, help="City name, e.g. 'San Francisco, CA'")
    parser.add_argument("--country", required=True, help="Country name, e.g. 'United States'")
    parser.add_argument(
        "--api-key",
        help="Numbeo API key (optional if NUMBEO_API_KEY is set in .env)",
    )
    args = parser.parse_args()

    # Resolve the API key: CLI flag takes precedence over .env file.
    env = load_env(Path(".env"))
    api_key = args.api_key or env.get("NUMBEO_API_KEY")
    if not api_key:
        print("Missing API key. Provide --api-key or set NUMBEO_API_KEY in .env")
        return 2

    # The Numbeo API expects a combined "City, Country" query parameter.
    query = f"{args.city}, {args.country}"
    encoded_query = urllib.parse.quote(query)

    items_url = f"{ITEMS_URL}?api_key={urllib.parse.quote(api_key)}"
    prices_url = f"{CITY_PRICES_URL}?query={encoded_query}&api_key={urllib.parse.quote(api_key)}"

    # Two API calls: items (catalog metadata) and city_prices (actual prices).
    items_resp = fetch_json(items_url)
    prices_resp = fetch_json(prices_url)

    items = items_resp.get("items", [])
    prices = prices_resp.get("prices", [])
    currency = prices_resp.get("currency", "")
    city_name = prices_resp.get("name", query)

    if not items or not prices:
        print("No data returned. Check the city/country and API key.")
        return 1

    items_index = build_items_index(items)
    rows = build_rows(prices, items_index, currency)

    headers = [
        "Order",
        "Category",
        "Item",
        "Average",
        "Lowest",
        "Highest",
        "Data Points",
    ]

    print(f"Numbeo cost-of-living prices for {city_name}")
    print(render_table(rows, headers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
