# Pantry Prices

Price the same grocery basket at two dates using Canadian retail prices. Select a series, geography, period and package quantities. The current scanner table also compares that basket across available geographies. [Open Pantry Prices](https://coolcode.ca/pantryprices/)

<!-- coolcode:guide -->
One 454 g butter, one 675 g white bread and a dozen eggs totalled $9.69 in September 2017 and $13.99 in September 2026 at Canadian scanner averages. Choose a province to compare its prices, or select an earlier price series to explore the published urban and national records back to 1914.
<!-- /coolcode:guide -->

## What the prices cover

| Source | Coverage | Geography and unit |
| --- | --- | --- |
| *Urban Retail Food Prices, 1914–59* | Annual, 1914–1959 | Five urban Canadian averages in cents per pound or dozen. [Original publication](https://publications.gc.ca/site/eng/9.843684/publication.html) |
| *Prices and Price Indexes*, Table 10 | Annual, 1960–1970 | Five urban Canadian averages in cents per pound or dozen from the printed annual columns. The 1957 methodology describes the urban sample of 33 cities. Each result links to its issue and physical PDF page. [Publication catalogue](https://publications.gc.ca/site/eng/9.822624/publication.html) · [Method, PDF p. 7](https://publications.gc.ca/collections/collection_2016/statcan/62-002/CS62-002-35-10-eng.pdf#page=7) |
| *Canada Year Book 2011*, Table 25.b and accompanying text | Matched basket in 1935 and 2008. Selected egg and milk benchmarks in 1960 and 1985 | Ten published package sizes cost $3.15 in 1935 and $55.04 in 2008. For 1985 the source reports eggs at $1.37 per dozen and partly skimmed milk at $0.98 per litre. Quart milk and partly skimmed milk appear as separate products. [Year Book source](https://www150.statcan.gc.ca/n1/pub/11-402-x/2011000/chap/prices-prix/prices-prix02-eng.htm) |
| Monthly retail price survey, 18-10-0002-01 | January 1995–February 2022 | Twelve groceries using national, population-weighted average prices from the CPI price collection, in Canadian dollars per specified package. The sample changed in May 2018. [Survey table](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810000201) |
| Monthly scanner prices, 18-10-0245-01 | From January 2017; September 2026 in this edition | Twelve groceries for Canada and all ten provinces. Available Whitehorse and Yellowknife prices begin in September 2025 and some products are withheld or absent. Prices come from participating retailers’ transactions, in dollars per displayed package or kilogram. More retailers entered in January 2024. [Scanner table](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810024501) · [Method](https://www150.statcan.gc.ca/n1/pub/62f0014m/62f0014m2022007-eng.htm) |

Between 1971 and 1994, only those two 1985 Year Book observations are included. Statistics Canada advises that the two monthly tables use different methods. Select one source per comparison. The overlap from January 2017 to February 2022 lets readers inspect both sets separately. Product specifications, outlets and brands can differ over time. The nominal basket totals describe what the published average prices imply for the chosen quantities. The CPI measures inflation.

## Comparing a basket

The first two historical sources use printed annual averages. For example, one pound of butter and five pounds of flour cost 53.6¢ in 1914 and 46.0¢ in 1935. The postwar items are first-grade creamery butter, white wrapped sliced bread, white all-purpose flour, fresh Grade A large eggs and granulated sugar. The monthly tables include 12 staples with the package sizes printed beside the quantity controls. A quantity of 0.25 means one quarter of the specified package.

Switch a monthly series to **Complete calendar year** for the unweighted mean of its 12 monthly prices. Incomplete calendar years do not appear. If an ingredient lacks even one price, its annual value and any basket using that ingredient are unreported. The same rule applies to monthly or regional basket totals when a selected item is missing. Individual ingredient prices stay visible in the breakdown. Downloads include the source, region, period, product, package, quantity, unit price, extended cost, statistical vector where available, and method.

## Refresh and verification

The monthly refresh downloads the two official CSV ZIP files, validates the expected dimensions, units, periods and product definitions, and checks the archived transcriptions and source manifest against their reviewed SHA-256 hashes. The checked-in browser edition records each modern source archive hash, source vector, monthly observation and retrieval date. The print transcriptions, publisher PDF hashes and dated historical review are in [sources](sources/). The historical verification date changes only after a reviewed update. Run `python3 scripts/refresh.py --verify-archives` to download and compare the eight original PDFs again. A failed source check leaves the previous combined edition available.

```sh
python3 scripts/refresh.py
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
```

The offline build uses the checked-in edition. Quantities and comparisons stay in the browser. GitHub Pages runs the interaction and mobile checks before deployment.

Adapted from Statistics Canada, *Urban Retail Food Prices*, *Prices and Price Indexes* and tables 18-10-0002-01 and 18-10-0245-01, reference periods shown above. This does not constitute an endorsement by Statistics Canada of this product. [Statistics Canada Open Licence](https://www.statcan.gc.ca/en/terms-conditions/open-licence)
