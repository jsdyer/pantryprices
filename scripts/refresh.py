"""Verify the scanned release and publish the checked annual price transcription."""
import csv
import hashlib
from http.cookiejar import CookieJar
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import build_opener, HTTPCookieProcessor, Request
from source_io import ROOT, archives, publish


class PublicationNotice(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pdf = None

    def handle_starttag(self, tag, attributes):
        if tag == "a":
            url = dict(attributes).get("href", "")
            if urlsplit(url).path.lower().endswith(".pdf"):
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
        if not notice.pdf or urljoin(page, notice.pdf) != source["url"]:
            raise ValueError("Publication notice did not link to the expected price report")
        request.add_header("Referer", page)
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


if __name__ == "__main__":
    verify(archives()[0])
    publish(assemble())
