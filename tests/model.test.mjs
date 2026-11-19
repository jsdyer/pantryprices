import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const edition = JSON.parse(
  readFileSync(new URL("../web/data/edition.json", import.meta.url), "utf8"),
);
import { basket } from "../web/model.mjs";
test("a basket sums published cents per original unit across years", () => {
  const amounts = { butter: 1, flour: 5, sugar: 0 };
  assert.equal(
    Number(basket(edition.items, amounts, 1914).total.toFixed(1)),
    53.6,
  );
  assert.equal(
    Number(basket(edition.items, amounts, 1935).total.toFixed(1)),
    46.0,
  );
  const result = basket(edition.items, { eggs: 0.25 }, 1914);
  assert.equal(result.lines[0].unit, "dozen");
  assert.equal(result.total, edition.items.eggs.prices[1914] / 4);
});
test("zero quantities produce an empty basket and each series covers all 46 years", () => {
  assert.deepEqual(basket(edition.items, { butter: 0 }, 1959), {
    lines: [],
    total: 0,
  });
  for (const { prices } of Object.values(edition.items))
    assert.equal(Object.keys(prices).length, 46);
});

import { prepareView } from "../web/model.mjs";

test("scanner regions keep package prices and incomplete years separate", () => {
  const canada = prepareView(edition, "scanner", "Canada", "monthly");
  const amounts = { butter: 1, bread: 1, eggs: 1 };
  assert.equal(basket(canada.items, amounts, "2017-09").total, 969);
  assert.equal(basket(canada.items, amounts, "2026-09").total, 1399);
  const north = prepareView(
    edition,
    "scanner",
    "Yellowknife, Northwest Territories",
    "monthly",
  );
  assert.equal(north.periods[0], "2025-09");
  assert.equal(basket(north.items, amounts, "2026-09").total, null);
  assert.equal(basket(north.items, { bread: 1 }, "2026-09").total, 435);
  const annual = prepareView(edition, "scanner", "Canada", "annual");
  assert.ok(annual.periods.includes("2025"));
  assert.equal(
    annual.items.butter.prices["2017"],
    canada.periods
      .filter((m) => m.startsWith("2017-"))
      .reduce((n, m) => n + canada.items.butter.prices[m], 0) / 12,
  );
});

test("survey, postwar print and source-page citations preserve their dates", () => {
  const old = prepareView(edition, "survey", "Canada", "monthly");
  assert.equal(old.periods[0], "1995-01");
  assert.equal(old.periods.at(-1), "2022-02");
  assert.equal(
    basket(old.items, { bread: 1, eggs: 1, butter: 1 }, "1995-01").total,
    566,
  );
  assert.equal(edition.tables.scanner.packages.milk.label, "Milk");
  assert.equal(edition.tables.survey.packages.milk.label, "Homogenized milk");
  const postwar = prepareView(edition, "print", "Urban Canada", "annual");
  assert.equal(
    basket(postwar.items, { butter: 1, flour: 5 }, "1970").total,
    133,
  );
  assert.equal(edition.tables.print.references["1970"].eggs.page, 70);
  assert.equal(edition.tables.print.count, 55);
});

test("published Year Book matched basket and partial benchmarks stay distinguishable", () => {
  const book = prepareView(edition, "yearbook", "Canada", "annual");
  const amounts = Object.fromEntries(
    Object.keys(book.items)
      .filter((k) => !["skimmed", "quart"].includes(k))
      .map((k) => [k, 1]),
  );
  assert.equal(basket(book.items, amounts, "1935").total, 315);
  assert.equal(basket(book.items, amounts, "2008").total, 5504);
  assert.equal(basket(book.items, amounts, "1985").total, null);
  assert.equal(basket(book.items, { eggs: 1, skimmed: 1 }, "1985").total, 235);
});
