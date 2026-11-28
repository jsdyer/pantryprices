"""Build the downloadable table and its search metadata from the same snapshot."""
import csv
from html import escape
import json


LEGACY_REGIONS = [{"key": "bc", "name": "British Columbia"}, {"key": "ns", "name": "Nova Scotia"}]


def price_summary(data):
    regions = data.get("regions", LEGACY_REGIONS)
    row = data["rows"][-1]
    items = []
    for region in sorted(regions, key=lambda item: item["name"]):
        code, name = escape(region["key"], quote=True), escape(region["name"])
        value = row.get(region["key"])
        price = "Unreported" if value is None else f"${value:.2f}"
        items.append(f'<tr><th scope="row"><a href="?coffeeProvince={code}#coffee">{name}</a></th><td>{price}</td></tr>')
    return (f'<table><caption>Average price for 340 g of roasted or ground coffee in {escape(row["month"])} '
            f'(Canadian dollars)</caption><thead><tr><th scope="col">Province</th><th scope="col">Shelf price</th>'
            f'</tr></thead><tbody>{"".join(items)}</tbody></table>')


def export_coffee(stage):
    data = json.loads((stage / "data/coffee.json").read_text())
    regions = data.get("regions", LEGACY_REGIONS)
    keys = [region["key"] for region in regions]
    with (stage / "data/coffee.csv").open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["month", "arabica_usd_per_kg", "cad_per_usd", "arabica_cad_per_kg",
                         *[key + "_cad_per_340g" for key in keys]])
        for row in data["rows"]:
            writer.writerow([row[key] for key in ("month", "usd", "fx", "cad", *keys)])
    base = "https://coolcode.ca/pantryprices/"
    return json.dumps({
        "@context": "https://schema.org", "@type": "Dataset", "@id": base + "#coffee",
        "name": "Commodity to shelf — monthly Arabica and Canadian retail coffee prices",
        "description": "Monthly World Bank Arabica prices in USD and CAD per kilogram, Bank of Canada exchange rates and average 340 g retail coffee prices from Statistics Canada across the provinces in this edition.",
        "creator": {"@type": "Organization", "name": "CoolCode", "url": "https://coolcode.ca/"},
        "url": base + "#coffee", "usageInfo": base + "#coffee-sources", "dateModified": data["retrieved"],
        "temporalCoverage": data["start"] + "/" + data["end"],
        "spatialCoverage": [region["name"] + ", Canada" for region in regions],
        "isBasedOn": [source["url"] for source in data["sources"]],
        "distribution": {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": base + "data/coffee.csv"}
    }, ensure_ascii=False).replace("<", "\\u003c")
