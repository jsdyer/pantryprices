"""Assemble the monthly coffee price comparison from three first-party sources."""
import csv
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO, TextIOWrapper
import json
import re
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from zipfile import ZipFile

from source_io import ROOT

MARKETS = "https://www.worldbank.org/en/research/commodity-markets"
FX = "https://www.bankofcanada.ca/valet/observations/FXMUSDCAD/json?start_date=2017-01-01"
SCANNER = "https://www150.statcan.gc.ca/n1/en/tbl/csv/18100245-eng.zip"
PRODUCT = "Roasted or ground coffee, 340 grams"
REGIONS = {"British Columbia": ("bc", "v1353834702"), "Nova Scotia": ("ns", "v1353834443")}


class WorkbookLink(HTMLParser):
    url = None

    def handle_starttag(self, tag, attrs):
        link = urljoin(MARKETS, dict(attrs).get("href") or "")
        loc = urlsplit(link)
        if (tag == "a" and loc.scheme == "https" and loc.hostname == "thedocs.worldbank.org"
                and loc.path.lower().endswith("/cmo-historical-data-monthly.xlsx")):
            self.url = link


def get(url):
    with urlopen(Request(url, headers={"User-Agent": "CoolCode.ca Pantry Prices/1.0"}), timeout=90) as response:
        return response.read()


def positive(value):
    number = Decimal(str(value))
    if not number.is_finite() or number <= 0:
        raise ValueError(f"Unexpected coffee observation: {value}")
    return number


def benchmark(payload):
    from openpyxl import load_workbook
    workbook = load_workbook(BytesIO(payload), read_only=True, data_only=True)
    try:
        rows = iter(workbook["Monthly Prices"].values)
        header = next(row for row in rows if "Coffee, Arabica" in row)
        column = header.index("Coffee, Arabica")
        if next(rows)[column] != "($/kg)":
            raise ValueError("Arabica benchmark unit changed")
        result = {}
        for row in rows:
            if not re.fullmatch(r"\d{4}M(0[1-9]|1[0-2])", str(row[0])):
                continue
            month = row[0].replace("M", "-")
            if month in result:
                raise ValueError("Duplicate benchmark month " + month)
            value = row[column]
            result[month] = None if value in (None, "…", "...", "..") else positive(value)
        return result
    finally:
        workbook.close()


def rates(payload):
    obj = json.loads(payload)
    metadata = obj["seriesDetail"]["FXMUSDCAD"]["metadata"]
    if metadata["unit"] != "Canadian dollars per US dollar" or metadata["frequency"] != "Monthly":
        raise ValueError("Bank of Canada changed the exchange-rate definition")
    result = {}
    for row in obj["observations"]:
        month = row["d"][:7]
        if month in result:
            raise ValueError("Duplicate exchange-rate month " + month)
        value = row.get("FXMUSDCAD", {}).get("v")
        result[month] = None if value in (None, "") else positive(value)
    return result


def shelf(payload):
    result = {"bc": {}, "ns": {}}
    with ZipFile(BytesIO(payload)) as archive, archive.open("18100245.csv") as raw:
        for row in csv.DictReader(TextIOWrapper(raw, encoding="utf-8-sig")):
            if row["Products"] != PRODUCT or row["GEO"] not in REGIONS:
                continue
            key, vector = REGIONS[row["GEO"]]
            if (row["UOM"], row["SCALAR_FACTOR"], row["VECTOR"]) != ("Dollars", "units", vector):
                raise ValueError("Review the retail coffee series or unit")
            month = row["REF_DATE"]
            value = row["VALUE"]
            if month in result[key] or row["STATUS"] not in (("",) if value else ("..", "...", "x", "F")):
                raise ValueError("Review duplicate or flagged retail coffee data at " + month)
            result[key][month] = positive(value) if value else None
    return result


def next_month(month):
    year, number = map(int, month.split("-"))
    return f"{year + (number == 12):04}-{number % 12 + 1:02}"


def compile_edition(workbook, fx, scanner, workbook_url):
    usd, cad, retail = benchmark(workbook), rates(fx), shelf(scanner)
    series = {"usd": usd, "fx": cad, **retail}
    last = {key: max(month for month, value in data.items() if value is not None) for key, data in series.items()}
    first = max(min(data) for data in series.values())
    end = min(last.values())
    if first != "2017-01" or end < "2026-09":
        raise ValueError("Coffee source coverage has shortened unexpectedly")
    rows = []
    month = first
    while month <= end:
        row = {key: data.get(month) for key, data in series.items()}
        row["cad"] = None if row["usd"] is None or row["fx"] is None else row["usd"] * row["fx"]
        rows.append({"month": month, **{key: None if value is None else float(value) for key, value in row.items()}})
        month = next_month(month)
    urls = [workbook_url, FX, SCANNER]
    blobs = [workbook, fx, scanner]
    return {"retrieved": datetime.now(timezone.utc).date().isoformat(), "start": first, "end": end,
            "latestBySource": last, "sources": [{"url": url, "sha256": sha256(blob).hexdigest()}
            for url, blob in zip(urls, blobs)], "rows": rows}


def save_edition(edition):
    destination = ROOT / "web/data/coffee.json"
    if destination.exists() and json.loads(destination.read_text())["end"] > edition["end"]:
        raise ValueError("Coffee edition ends before the last successful release")
    destination.write_text(json.dumps(edition, separators=(",", ":"), allow_nan=False) + "\n")


def collect(scanner):
    link = WorkbookLink()
    link.feed(get(MARKETS).decode("utf-8"))
    if not link.url:
        raise ValueError("Monthly Pink Sheet link missing from World Bank commodity markets")
    return compile_edition(get(link.url), get(FX), scanner, link.url)
