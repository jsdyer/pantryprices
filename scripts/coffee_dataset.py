"""Build the downloadable table and its search metadata from the same snapshot."""
import csv
import json


def export_coffee(stage):
    data = json.loads((stage / "data/coffee.json").read_text())
    with (stage / "data/coffee.csv").open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["month", "arabica_usd_per_kg", "cad_per_usd", "arabica_cad_per_kg",
                         "bc_cad_per_340g", "ns_cad_per_340g"])
        for row in data["rows"]:
            writer.writerow([row[key] for key in ("month", "usd", "fx", "cad", "bc", "ns")])
    base = "https://coolcode.ca/pantryprices/"
    return json.dumps({
        "@context": "https://schema.org", "@type": "Dataset", "@id": base + "#coffee",
        "name": "Commodity to shelf — monthly Arabica and Canadian retail coffee prices",
        "description": "Monthly World Bank Arabica prices in USD and CAD per kilogram, Bank of Canada exchange rates and average 340 g retail coffee prices from Statistics Canada for British Columbia and Nova Scotia.",
        "creator": {"@type": "Organization", "name": "CoolCode", "url": "https://coolcode.ca/"},
        "url": base + "#coffee", "usageInfo": base + "#coffee-sources", "dateModified": data["retrieved"],
        "temporalCoverage": data["start"] + "/" + data["end"],
        "spatialCoverage": ["British Columbia, Canada", "Nova Scotia, Canada"],
        "isBasedOn": [source["url"] for source in data["sources"]],
        "distribution": {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": base + "data/coffee.csv"}
    }, ensure_ascii=False).replace("<", "\\u003c")
