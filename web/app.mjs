import {
  byId,
  choices,
  element,
  facts,
  table,
  sourceLink,
  downloadCsv,
  loadEdition,
  failed,
} from "./ui.mjs";
import { basket, prepareView } from "./model.mjs";

const money = (n) =>
  n === null
    ? "Unreported"
    : (n / 100).toLocaleString("en-CA", { style: "currency", currency: "CAD" });
const cents = (n) =>
  n === null
    ? "Unreported"
    : n.toLocaleString("en-CA", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 2,
      }) + "¢";
function periodLabel(period) {
  if (period.length === 4) return period;
  const [year, month] = period.split("-");
  return new Intl.DateTimeFormat("en-CA", {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(Number(year), Number(month) - 1)));
}

try {
  const data = await loadEdition("published prices");
  const tables = data.tables;
  const sourceChoices = Object.entries(tables).map(([id, x]) => [
    id,
    x.label + " · " + x.start + " to " + x.end,
  ]);
  choices("series", [
    ...sourceChoices,
    ["urban", "Urban annual prices · 1914 to 1959"],
  ]);
  let view,
    inputs = {},
    csv = [];
  let seriesId, monthly, annual, presets;

  function sourceFor(item, period) {
    if (seriesId === "urban")
      return {
        label: "PDF page " + item.page,
        url: data.source + "#page=" + item.page,
      };
    if (seriesId === "yearbook")
      return {
        label: "Year Book source",
        url: "https://www150.statcan.gc.ca/n1/pub/11-402-x/2011000/chap/prices-prix/prices-prix02-eng.htm",
      };
    const specific = tables[seriesId].references?.[period]?.[item.key];
    if (specific)
      return {
        label: "PDF page " + specific.page,
        url: specific.url + "#page=" + specific.page,
      };
    const vector = view.items[item.key].vector;
    return vector
      ? { label: vector, url: view.source }
      : { label: "Source table", url: view.source };
  }

  function selectPeriods() {
    const periods = view.periods;
    for (const id of ["first", "second"])
      choices(
        id,
        periods.map((date) => [date, periodLabel(date)]),
      );
    if (!periods.length) return;
    let first = periods[0];
    if (monthly && !annual) {
      const latestMonth = periods.at(-1).slice(5);
      first = periods.find((p) => p.endsWith("-" + latestMonth)) || first;
    }
    byId("first").value = first;
    byId("second").value = seriesId === "urban" ? "1935" : periods.at(-1);
  }

  function configure(updateIngredients) {
    seriesId = byId("series").value;
    const series = tables[seriesId];
    monthly = series?.frequency === "monthly";
    if (updateIngredients) {
      const regions = series ? Object.keys(series.regions) : ["Urban Canada"];
      choices(
        "region",
        regions.map((name) => [name, name]),
      );
      byId("region").value = regions.includes("Canada") ? "Canada" : regions[0];
      byId("frequency").value = "monthly";
    }
    const region = byId("region").value;
    byId("region").disabled = !series || Object.keys(series.regions).length < 2;
    byId("frequency-wrap").hidden = !monthly;
    annual = monthly && byId("frequency").value === "annual";
    view = prepareView(data, seriesId, region, byId("frequency").value);
    const annualDescription = annual
      ? " Annual values are unweighted means of 12 published monthly prices; incomplete product-years remain unreported."
      : "";
    byId("method").textContent = view.method + annualDescription;
    if (updateIngredients) {
      presets = !monthly
        ? { butter: 1, flour: 5 }
        : { butter: 1, bread: 1, eggs: 1 };
      if (seriesId === "yearbook")
        presets = Object.fromEntries(
          Object.keys(view.items)
            .filter((key) => !["skimmed", "quart"].includes(key))
            .map((key) => [key, 1]),
        );
      if (!Object.keys(presets).some((k) => k in view.items))
        presets = { [Object.keys(view.items)[0]]: 1 };
      inputs = {};
      byId("ingredients").replaceChildren();
      for (const [key, item] of Object.entries(view.items)) {
        const label = element("label", item.label + " (" + item.unit + ")"),
          input = element("input");
        Object.assign(input, {
          type: "number",
          min: "0",
          max: "1000",
          step: "0.25",
          value: presets[key] || 0,
        });
        label.append(input);
        byId("ingredients").append(label);
        inputs[key] = input;
      }
    }
    const previous = [byId("first").value, byId("second").value];
    selectPeriods();
    if (!updateIngredients) {
      for (const [index, id] of ["first", "second"].entries()) {
        const candidate = annual
          ? previous[index].slice(0, 4)
          : previous[index];
        if (view.periods.includes(candidate)) byId(id).value = candidate;
      }
    }
    render();
  }

  function render() {
    const format = ["urban", "print"].includes(seriesId) ? cents : money;
    const dates = [byId("first").value, byId("second").value];
    const quantities = Object.fromEntries(
      Object.entries(inputs).map(([k, input]) => [k, input.valueAsNumber || 0]),
    );
    for (const id of [
      "facts",
      "breakdown",
      "annual",
      "trend",
      "axis",
      "regional",
    ])
      byId(id).replaceChildren();
    byId("csv").disabled = true;
    csv = [];
    if (
      !view.periods.length ||
      Object.values(inputs).some((i) => !i.validity.valid)
    ) {
      byId("finding").textContent = view.periods.length
        ? "Use quantities from 0 to 1,000 in quarter units."
        : "This geography has no complete calendar year yet. Choose monthly prices.";
      return;
    }
    const [a, b] = dates.map((p) => basket(view.items, quantities, p));
    if (!a.lines.length) {
      byId("finding").textContent =
        "Choose a positive quantity to price your basket.";
      return;
    }
    const change =
      a.total === null || b.total === null ? null : b.total - a.total;
    facts("facts", [
      [periodLabel(dates[0]), format(a.total)],
      [periodLabel(dates[1]), format(b.total)],
      [
        "Change in basket cost",
        change === null
          ? "Unreported"
          : (change > 0 ? "+" : "") + format(change),
      ],
    ]);
    const missing = [
      ...new Set(
        [...a.lines, ...b.lines]
          .filter((l) => l.unitCents === null)
          .map((l) => l.label),
      ),
    ];
    byId("finding").textContent = missing.length
      ? "A complete basket needs a reported price for " +
        missing.join(", ") +
        ". The table identifies the missing periods."
      : "The same quantities are priced in nominal Canadian dollars for " +
        view.region +
        ".";
    table(
      "breakdown",
      [
        "Item",
        "Quantity",
        ...dates.map((p) => periodLabel(p) + " unit price"),
        ...dates.map((p) => periodLabel(p) + " cost"),
        "Source",
      ],
      a.lines.map((line, i) => {
        const first = sourceFor(line, dates[0]),
          second = sourceFor(b.lines[i], dates[1]);
        const sources = element("div");
        sources.append(sourceLink(first.label, first.url));
        if (first.url !== second.url)
          sources.append(" · ", sourceLink(second.label, second.url));
        return [
          line.label,
          line.quantity + " × " + line.unit,
          format(line.unitCents),
          format(b.lines[i].unitCents),
          format(line.costCents),
          format(b.lines[i].costCents),
          sources,
        ];
      }),
    );
    const trend = view.periods.map((p) => [
      p,
      basket(view.items, quantities, p).total,
    ]);
    const shown =
      monthly && !annual
        ? trend.filter(([p]) => p.slice(0, 4) === dates[1].slice(0, 4))
        : trend;
    const max = Math.max(1, ...shown.map(([, value]) => value ?? 0));
    byId("chart-label").textContent =
      monthly && !annual
        ? "Monthly costs in " +
          dates[1].slice(0, 4) +
          ". Choose a bar to change the comparison month."
        : "Choose a bar to change the comparison year.";
    for (const [period, value] of shown) {
      const button = element("button"),
        bar = element("span");
      button.title = periodLabel(period) + " · " + format(value);
      button.setAttribute("aria-label", button.title);
      button.setAttribute("aria-pressed", String(period === dates[1]));
      if (value === null) button.className = "missing";
      else bar.style.height = (100 * value) / max + "%";
      button.append(bar);
      button.onclick = () => {
        byId("second").value = period;
        render();
        byId("trend").querySelector('[aria-pressed="true"]').focus();
      };
      byId("trend").append(button);
    }
    byId("axis").append(
      element("span", periodLabel(shown[0][0])),
      element("span", periodLabel(shown.at(-1)[0])),
    );
    table(
      "annual",
      ["Period", "Basket cost"],
      trend.map(([p, v]) => [periodLabel(p), format(v)]),
    );
    const regions = Object.keys(tables[seriesId]?.regions || {});
    byId("region-comparison").hidden = regions.length < 2;
    if (regions.length > 1) {
      const comparison = regions
        .map((name) => [
          name,
          basket(
            prepareView(data, seriesId, name, byId("frequency").value).items,
            quantities,
            dates[1],
          ).total,
        ])
        .sort((a, b) => (a[1] ?? Infinity) - (b[1] ?? Infinity));
      table(
        "regional",
        ["Geography", periodLabel(dates[1]) + " basket cost"],
        comparison.map(([name, value]) => [name, format(value)]),
      );
    }
    csv = [
      [
        "source_series",
        "geography",
        "period",
        "frequency",
        "item",
        "quantity",
        "package",
        "unit_price_CAD",
        "cost_CAD",
        "source",
        "vector",
        "method",
      ],
    ];
    for (const [i, comparison] of [a, b].entries())
      for (const line of comparison.lines) {
        const dollars = (n) => (n === null ? "" : +(n / 100).toFixed(6));
        csv.push([
          byId("series").selectedOptions[0].textContent,
          view.region,
          dates[i],
          annual
            ? "12-month arithmetic mean"
            : monthly
              ? "published month"
              : "published year",
          line.label,
          line.quantity,
          line.unit,
          dollars(line.unitCents),
          dollars(line.costCents),
          sourceFor(line, dates[i]).url,
          view.items[line.key].vector || "",
          byId("method").textContent,
        ]);
      }
    byId("csv").disabled = false;
  }

  byId("series").onchange = () => configure(true);
  byId("region").onchange = byId("frequency").onchange = () => configure(false);
  for (const id of ["first", "second"]) byId(id).onchange = render;
  byId("ingredients").oninput = render;
  byId("reset").onclick = () => {
    for (const [key, input] of Object.entries(inputs))
      input.value = presets[key] || 0;
    render();
  };
  byId("csv").onclick = () => downloadCsv("pantry-prices-comparison.csv", csv);
  configure(true);
} catch (error) {
  console.error(error);
  failed();
}
