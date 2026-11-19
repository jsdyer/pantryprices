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
