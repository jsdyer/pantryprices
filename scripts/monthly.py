"""Select published package prices from Statistics Canada's two distinct retail tables."""
import csv
from decimal import Decimal
from hashlib import sha256
from io import BytesIO, TextIOWrapper
from urllib.request import Request, urlopen
from zipfile import ZipFile

TABLES = {
    "scanner": ("18100245", "Retail scanner prices", "Average prices from transactions at participating grocery retailers. Product mixes can change. Additional retailers entered the sample in January 2024. Whitehorse and Yellowknife first appear in September 2025."),
    "survey": ("18100002", "Retail price survey", "National averages from the CPI price collection, weighted by area population. Brands and outlets varied. The sample changed in May 2018. Statistics Canada discontinued this table after February 2022."),
}

# Each input is the publisher’s exact item specification. The tables overlap but
# differ in sampling and product definitions; they have separate series IDs.
PRODUCTS = {
    "butter": ("Butter, 454 grams", "Butter, 454 grams"),
    "flour": ("Wheat flour, 2.5 kilograms", "Flour, 2.5 kilograms"),
    "bread": ("White bread, 675 grams", "Bread, 675 grams"),
    "eggs": ("Eggs, 1 dozen", "Eggs, 1 dozen"),
    "sugar": ("White sugar, 2 kilograms", "Sugar, white, 2 kilograms"),
    "milk": ("Milk, 1 litre", "Homogenized milk, 1 litre"),
    "beef": ("Ground beef, per kilogram", "Ground beef, 1 kilogram"),
    "apples": ("Apples, per kilogram", "Apples, 1 kilogram"),
    "bananas": ("Bananas, per kilogram", "Bananas, 1 kilogram"),
    "potatoes": ("Potatoes, 4.54 kilograms", "Potatoes, 4.54 kilograms"),
    "onions": ("Onions, per kilogram", "Onions, 1 kilogram"),
    "carrots": ("Carrots, 1.36 kilograms", "Carrots, 1 kilogram"),
}


def download(code):
    url = f"https://www150.statcan.gc.ca/n1/en/tbl/csv/{code}-eng.zip"
    with urlopen(Request(url, headers={"User-Agent": "CoolCode.ca Pantry Prices/1.0"}), timeout=100) as response:
        return response.read()


def read_table(key, payload):
    code, label, method = TABLES[key]
    position = 0 if key == "scanner" else 1
    specs = {names[position]: item for item, names in PRODUCTS.items()}
    records = {}
    vectors = {}
    periods = set()
    count = 0
    with ZipFile(BytesIO(payload)) as archive, archive.open(code + ".csv") as member:
        rows = csv.DictReader(TextIOWrapper(member, encoding="utf-8-sig"))
        product_column = next(name for name in rows.fieldnames if name in ("Products", "Products and product groups"))
        for row in rows:
            name = row[product_column].strip()
            if name not in specs:
                continue
            if row["UOM"] != "Dollars" or row["SCALAR_FACTOR"] != "units":
                raise ValueError("Unexpected source unit for " + name)
            item, region, month = specs[name], row["GEO"], row["REF_DATE"]
            regions = records.setdefault(region, {})
            values = regions.setdefault(item, {})
            if month in values:
                raise ValueError(f"Duplicate {key} {region} {name} {month}")
            price = row["VALUE"]
            if price:
                cents = Decimal(price) * 100
                if cents <= 0 or cents != cents.to_integral_value() or row["STATUS"] not in ("",):
                    raise ValueError(f"Review new price or quality flag: {row}")
                values[month] = int(cents)
                count += 1
            else:
                if row["STATUS"] not in ("..", "...", "x", "F"):
                    raise ValueError(f"Review missing value: {row}")
                values[month] = None
            vector = vectors.setdefault(region, {}).setdefault(item, row["VECTOR"])
            if row["VECTOR"] != vector:
                raise ValueError("Source vector changed within series")
            periods.add(month)
    dates = sorted(periods)
    if len(records.get("Canada", {})) != len(specs) or not dates:
        raise ValueError(f"Missing products in table {code}")
    required = ("2017-01", "2026-09") if key == "scanner" else ("1995-01", "2022-02")
    if dates[0] != required[0] or dates[-1] < required[1]:
        raise ValueError(f"Truncated source periods in {code}")
    data = {}
    for region, items in records.items():
        region_dates = sorted(set().union(*(values.keys() for values in items.values())))
        data[region] = {"periods": region_dates, "values": {item: [values.get(d) for d in region_dates]
                            for item, values in ((item, items.get(item, {})) for item in specs.values())}, "vectors": vectors[region]}
    packages = {}
    for name, item in specs.items():
        title, unit = name.rsplit(", ", 1)
        packages[item] = {"label": title, "unit": unit.replace("per kilogram", "1 kilogram")}
    return dict(label=label, frequency="monthly", start=dates[0], end=dates[-1], count=count,
                id=code, source=f"https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid={code}01",
                archive=f"https://www150.statcan.gc.ca/n1/en/tbl/csv/{code}-eng.zip",
                archiveSha256=sha256(payload).hexdigest(), method=method, packages=packages, regions=data)
