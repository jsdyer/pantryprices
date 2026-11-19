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
import { basket } from "./model.mjs";
const cents = (n) =>
  n.toLocaleString("en-CA", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 2,
  }) + "¢";
try {
  const data = await loadEdition("item-year prices");
  const items = data.items;
  const defaults = { butter: 1, flour: 5 };
  for (const id of ["first", "second"])
    choices(
      id,
      data.years.map((y) => [y, y]),
    );
  byId("first").value = 1914;
  byId("second").value = 1935;
  const inputs = {};
  for (const [key, item] of Object.entries(items)) {
    const label = element("label", item.label + " (" + item.unit + ")"),
      input = element("input");
    input.type = "number";
    input.min = "0";
    input.max = "1000";
    input.step = "0.25";
    input.value = defaults[key] || 0;
    label.append(input);
    byId("ingredients").append(label);
    inputs[key] = input;
  }
  let csv;
  function render() {
    const quantities = Object.fromEntries(
      Object.entries(inputs).map(([key, input]) => [
        key,
        input.valueAsNumber || 0,
      ]),
    );
    const years = [+byId("first").value, +byId("second").value];
    if (Object.values(inputs).some((input) => !input.validity.valid)) {
      byId("facts").replaceChildren();
      byId("breakdown").replaceChildren();
      byId("annual").replaceChildren();
      byId("trend").replaceChildren();
      byId("csv").disabled = true;
      byId("finding").textContent =
        "Use quantities from 0 to 1,000 in quarter units.";
      return;
    }
    const [a, b] = years.map((y) => basket(items, quantities, y));
    facts("facts", [
      [String(years[0]), cents(a.total)],
      [String(years[1]), cents(b.total)],
      [
        "Change in basket cost",
        (b.total > a.total ? "+" : "") + cents(b.total - a.total),
      ],
    ]);
    byId("finding").textContent = a.lines.length
      ? "Costs use the same quantities in both years. Each price is in Canadian cents."
      : "Choose a positive quantity to price your basket.";
    const hs = [
      "Item",
      "Quantity",
      years[0] + " unit price",
      years[0] + " cost",
      years[1] + " unit price",
      years[1] + " cost",
      "Original table",
    ];
    table(
      "breakdown",
      hs,
      a.lines.map((r, i) => [
        r.label,
        r.quantity + " " + r.unit,
        cents(r.unitCents),
        cents(r.costCents),
        cents(b.lines[i].unitCents),
        cents(b.lines[i].costCents),
        sourceLink(
          "Printed p. " + (r.page + 1),
          data.source + "#page=" + r.page,
        ),
      ]),
    );
    const trend = data.years.map((y) => [
        y,
        basket(items, quantities, y).total,
      ]),
      max = Math.max(1, ...trend.map((x) => x[1]));
    byId("trend").replaceChildren(
      ...trend.map(([year, value]) => {
        const button = element("button"),
          bar = element("span");
        button.title = year + " · " + cents(value);
        button.setAttribute("aria-label", button.title);
        button.setAttribute("aria-pressed", String(year === years[1]));
        bar.style.height = (100 * value) / max + "%";
        button.append(bar);
        button.onclick = () => {
          byId("second").value = year;
          render();
          byId("trend").querySelector('[aria-pressed="true"]').focus();
        };
        return button;
      }),
    );
    table(
      "annual",
      ["Year", "Basket cost"],
      trend.map(([y, v]) => [y, cents(v)]),
    );
    csv = [
      [
        "year",
        "item",
        "quantity",
        "unit",
        "unit_price_cents",
        "cost_cents",
        "source_page",
      ],
    ];
    for (const [i, store] of [a, b].entries())
      for (const r of store.lines)
        csv.push([
          years[i],
          r.label,
          r.quantity,
          r.unit,
          r.unitCents,
          +r.costCents.toFixed(3),
          data.source + "#page=" + r.page,
        ]);
    byId("csv").disabled = !a.lines.length;
  }
  byId("reset").onclick = () => {
    for (const [key, input] of Object.entries(inputs))
      input.value = defaults[key] || 0;
    render();
  };
  byId("csv").onclick = () => downloadCsv("historical-grocery-basket.csv", csv);
  document.querySelector("main").addEventListener("input", render);
  render();
} catch {
  failed();
}
