# Pantry Prices

Choose quantities of butter, flour, bread, eggs and granulated sugar and compare the cost of the same basket in two years. Select an annual bar to inspect that year’s prices.

[Open Pantry Prices](https://coolcode.ca/pantryprices/)

## Try it

<!-- coolcode:guide -->
One pound of butter and five pounds of flour cost 53.6¢ in 1914 and 46.0¢ in 1935 at the published urban Canadian averages. Change either quantity to see how much that ingredient contributes.
<!-- /coolcode:guide -->

## Sources and interpretation

The Dominion Bureau of Statistics published *Urban Retail Food Prices, 1914–59* in 1960. The five annual series have 46 observations each. Prices are Canadian cents per pound, except eggs, which are priced by the dozen. Entries use the printed annual averages. Set an ingredient to zero to remove it, or enter quarter-unit quantities for a smaller basket.

The totals use nominal prices in each year. The report discusses changes to collection methods and product specifications. The figures describe urban Canada and cannot give a Halifax shop’s price or a family’s actual grocery bill. Each ingredient links to the original price table, and the CSV includes quantity, units, price, calculated cost and source page for both years.

[Publication record](https://publications.gc.ca/site/eng/9.843684/publication.html) · [Transcribed annual series](sources/annual-prices.csv)

## Refresh and verification

Monthly. The importer checks the scanned report against its reviewed version and validates the annual prices using the Python standard library. The retrieval date records the last successful source check in UTC. The coverage on the homepage and in the tool describes the underlying records. A changed archive requiring review or a failed download leaves the previous edition available. The scheduled workflow validates the data, runs the tests and publishes the resulting snapshot. For a manual refresh, run `python3 scripts/refresh.py`.

The interface, selections and CSV exports run locally in the browser. Visiting a source or map link opens the publisher’s site. The offline build uses the checked-in edition. To build and preview it, run the following commands.

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

The Pages workflow also exercises the tool in Chromium at its project subpath and checks the mobile layout. Update the source sentence in `tool.json` and the marked guide above when changing coverage or interpretation.
