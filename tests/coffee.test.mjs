import test from "node:test";
import assert from "node:assert/strict";
import { compare } from "../web/coffee.mjs";
const rows = [
  { month: "2024-01", cad: 8, bc: 10, ns: 12 },
  { month: "2024-02", cad: 8.8, bc: null, ns: 10.8 },
  { month: "2024-03", cad: 8.9, bc: 11, ns: 12.6 },
];
test("uses each series' own shared-month baseline and counts first published crossing", () => {
  const result = compare(rows, "2024-01", "2024-03", 10);
  assert.deepEqual(result.points[0].changes, { cad: 0, bc: 0, ns: 0 });
  assert.equal(result.points[1].changes.bc, null);
  assert.deepEqual(result.crossings, { cad: 1, bc: 2, ns: null });
  assert.deepEqual(compare(rows, "2024-01", "2024-02", -10).crossings, { cad: null, bc: null, ns: 1 });
  assert.throws(() => compare(rows, "2024-02", "2024-03", 10), /base month/);
});
