"""Read the reviewed year-only columns of Canada's printed retail price tables."""
import csv
from source_io import ROOT, archives


def read_print_series(yearbook=False):
    filename = "yearbook-prices.csv" if yearbook else "postwar-prices.csv"
    allowed = {source["url"] for source in archives()[1:]}
    packages, rows, citations = {}, {}, {}
    with (ROOT / "sources" / filename).open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            year, item, url = row["period"], row["item"], row["source_url"]
            number, price = int(row["pdf_page"]), float(row["cents"])
            if url not in allowed or number < 1 or price <= 0 or len(year) != 4 or not year.isdigit():
                raise ValueError("Invalid price or unreviewed archive citation")
            spec = {"label": row["label"], "unit": row["unit"]}
            if packages.setdefault(item, spec) != spec or item in rows.setdefault(year, {}):
                raise ValueError("Inconsistent unit or duplicate printed price")
            rows[year][item] = price
            citations.setdefault(year, {})[item] = dict(url=url, page=number)
    periods = sorted(rows)
    if not periods or (not yearbook and any(set(prices) != set(packages) for prices in rows.values())):
        raise ValueError("Incomplete printed annual observations")
    values = {item: [rows[year].get(item) for year in periods] for item in packages}
    geography = "Canada" if yearbook else "Urban Canada"
    postwar_method = "Published annual retail price averages for urban Canada. Butter is first-grade creamery; bread is white, wrapped and sliced; flour is white all-purpose; eggs are fresh Grade A large. Sugar is granulated. Prices are cents per pound or dozen."
    yearbook_method = "Statistics Canada aligned ten package sizes for 1935 and 2008 in Table 25.b. The default basket is one of each. The article also gives individual egg and milk observations for 1960 and 1985. Other items in those years have no reported price. Quart milk and partly skimmed milk are separate specifications."
    return dict(label="Canada Year Book benchmarks" if yearbook else "Printed urban food tables", frequency="annual", start=periods[0], end=periods[-1],
                count=sum(len(values) for values in rows.values()), source=next(iter(citations[periods[0]].values()))["url"],
                method=yearbook_method if yearbook else postwar_method,
                packages=packages, references=citations, regions={geography: {"periods": periods, "values": values}})
