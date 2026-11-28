export const series = [
  { key: "cad", name: "Arabica benchmark", colour: "#733e22", dash: "" },
  { key: "bc", name: "British Columbia", colour: "#186b64", dash: "9 4" },
  { key: "ns", name: "Nova Scotia", colour: "#584687", dash: "3 3" },
];

export function seriesFor(first, second) {
  return [series[0], { ...series[1], ...first }, { ...series[2], ...second }];
}

export function change(value, base) {
  return Number.isFinite(value) && base > 0 ? (value - base) / base * 100 : null;
}

export function compare(rows, start, end, threshold, selectedSeries = series) {
  const selected = rows.filter(row => row.month >= start && row.month <= end);
  const base = selected[0];
  if (!base || base.month !== start || selectedSeries.some(s => !(base[s.key] > 0))) {
    throw new Error("Choose a base month with all three published prices.");
  }
  const points = selected.map(row => ({
    row,
    changes: Object.fromEntries(selectedSeries.map(({ key }) => [key, change(row[key], base[key])])),
  }));
  const crossings = Object.fromEntries(selectedSeries.map(({ key }) => {
    const index = points.findIndex(({ changes }) => {
      const value = changes[key];
      return value !== null && (threshold > 0 ? value >= threshold - 1e-9 : value <= threshold + 1e-9);
    });
    return [key, index < 0 ? null : index];
  }));
  return { points, crossings };
}
