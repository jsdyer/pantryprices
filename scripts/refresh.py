"""Verify the scanned release and publish the checked annual price transcription."""
import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
import hashlib
from http.cookiejar import CookieJar
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import build_opener, HTTPCookieProcessor, Request
from source_io import ROOT, archives, publish
from monthly import TABLES, download, read_table
from print_prices import read_print_series


class PublicationNotice(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pdf = None

    def handle_starttag(self, tag, attributes):
        if tag == "a":
            url = dict(attributes).get("href", "")
            if urlsplit(url).path.lower().endswith(".pdf") and "/fr/" not in url and "fra.pdf" not in url:
                self.pdf = url


def verify(source):
    # The publisher may interpose its archived-content notice with a Continue link.
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    request = Request(source["url"], headers={"User-Agent":"CoolCode.ca historical prices/1.0"})
    with opener.open(request, timeout=100) as response:
        data = response.read()
        page = response.geturl()
    if not data.startswith(b"%PDF"):
        notice = PublicationNotice()
        notice.feed(data.decode())
        target = urljoin(page, notice.pdf or "")
        valid_chapter = source.get("chapter") and target.split("?")[0] == source["chapter"]
        if not notice.pdf or (target != source["url"] and not valid_chapter):
            raise ValueError("Publication notice did not link to the expected price report")
        request = Request(target, headers={"Referer": page, "User-Agent": "CoolCode.ca historical prices/1.0"})
        with opener.open(request, timeout=100) as response:
            data = response.read()
    if hashlib.sha256(data).hexdigest() != source["sha256"]:
        raise ValueError("Review the changed price report before updating the transcription")


def assemble():
    items = {}
    with (ROOT / "sources/annual-prices.csv").open() as raw:
        for row in csv.DictReader(raw):
            item = items.setdefault(row["item"], dict(label=row["label"], unit=row["unit"], page=int(row["pdf_page"]), prices={}))
            year = int(row["year"])
            price = float(row["cents"])
            if year in item["prices"] or price <= 0 or (row["unit"], int(row["pdf_page"])) != (item["unit"], item["page"]):
                raise ValueError("Invalid or duplicate price")
            item["prices"][year] = price
    years = list(range(1914, 1960))
    if not items or any(sorted(item["prices"]) != years for item in items.values()):
        raise ValueError("Incomplete annual series")
    return dict(start=years[0], end=years[-1], coverage="Urban Canada, 1914–1959", count=len(items)*len(years),
                items=items, years=years, source=archives()[0]["url"])


def check_review():
    folder = ROOT / "sources"
    review = json.loads((folder / "historical-review.json").read_text())
    for name, expected in review["sha256"].items():
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Historical source or transcription needs review: {name}")
    return review["verified"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-archives", action="store_true",
                        help="Re-download the eight original PDFs and compare bytes to reviewed hashes")
    args = parser.parse_args()
    historical_verified = check_review()
    if args.verify_archives:
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(verify, archives()))
        print("All archived PDF digests match the historical review.")
    data = assemble()
    data["historicalVerified"] = historical_verified
    data["tables"] = {key: read_table(key, download(spec[0])) for key, spec in TABLES.items()}
    data["tables"]["print"] = read_print_series()
    data["tables"]["yearbook"] = read_print_series(yearbook=True)
    data["count"] += sum(table["count"] for table in data["tables"].values())
    data["recentStart"] = data["tables"]["scanner"]["start"]
    data["recentEnd"] = data["tables"]["scanner"]["end"]
    previous_path = ROOT / "web/data/edition.json"
    if previous_path.exists():
        previous = json.loads(previous_path.read_text())
        if previous.get("recentEnd", "") > data["recentEnd"]:
            raise ValueError("Scanner edition ends before the last successful release")
    data["end"] = int(data["recentEnd"][:4])
    data["coverage"] = "Selected Canadian series, 1914–" + str(data["end"])
    publish(data)
