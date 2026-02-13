# Numbeo Cost-of-Living Example (Python)

A command-line tool that fetches cost-of-living data from the
[Numbeo API](https://www.numbeo.com/common/api.jsp) and displays it as a sorted ASCII
table. For any city/country pair it shows average, lowest, and highest prices
grouped by category. Please check [our API documentation](https://www.numbeo.com/api/doc.jsp)

## Requirements

- Python 3.8+
- A valid [Numbeo API key](https://www.numbeo.com/common/api.jsp)
- No third-party packages (uses only the standard library)

## Quick start

```bash
python app.py --city "San Francisco, CA" --country "United States" --api-key YOUR_KEY
```

Instead of passing the key every time you can store it in a `.env` file
(auto-loaded at startup):

```
NUMBEO_API_KEY=YOUR_KEY
```

## CLI options

| Flag          | Required | Description                                            |
|---------------|----------|--------------------------------------------------------|
| `--city`      | Yes      | City name, e.g. `"San Francisco, CA"` or `"Belgrade"`. |
| `--country`   | Yes      | Country name, e.g. `"United States"` or `"Serbia"`.    |
| `--api-key`   | No       | Numbeo API key. Falls back to `NUMBEO_API_KEY` in `.env`. |

## How it works

1. **Fetch item catalog** -- calls `/api/items` to get each item's
   `display_order`, `category`, and `name`.
2. **Fetch city prices** -- calls `/api/city_prices` with a combined
   `"City, Country"` query to get average, lowest, and highest prices.
3. **Join and sort** -- prices are matched to item metadata by `item_id` and
   sorted by `display_order` then item name.
4. **Render** -- results are printed as a left-aligned ASCII table.

## Example output

```
Numbeo cost-of-living prices for San Francisco, CA, United States
Order | Category    | Item                          | Average       | Lowest       | Highest
------+-------------+-------------------------------+---------------+--------------+--------
1     | Restaurants | Meal, Inexpensive Restaurant   | 25.00 USD     | 15.00 USD    | 40.00 USD
2     | Restaurants | Meal for 2 People, Mid-range   | 100.00 USD    | 60.00 USD    | 150.00 USD
...
```

## API endpoints used

- `https://www.numbeo.com/api/items?api_key=...`
- `https://www.numbeo.com/api/city_prices?query=City,Country&api_key=...`

## Project structure

```
.
├── app.py        # Main application
├── .env          # API key (git-ignored)
├── .gitignore
└── README.md
```
