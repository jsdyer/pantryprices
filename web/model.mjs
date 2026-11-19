export function basket(items, quantities, period) {
  const lines = Object.entries(items)
    .filter(([key]) => quantities[key] > 0)
    .map(([key, item]) => {
      const unitCents = item.prices[period] ?? null;
      return {
        key,
        label: item.label,
        unit: item.unit,
        page: item.page,
        quantity: quantities[key],
        unitCents,
        costCents: unitCents === null ? null : quantities[key] * unitCents,
      };
    });
  const total = lines.some((line) => line.costCents === null)
    ? null
    : lines.reduce((sum, line) => sum + line.costCents, 0);
  return { lines, total };
}

export function prepareView(data, sourceId, region, frequency) {
  if (sourceId === "urban") {
    return {
      periods: data.years.map(String),
      items: data.items,
      region: "Urban Canada",
      source: data.source,
      method:
        "Published annual urban Canadian averages in cents per pound or dozen. Specifications and collection practices changed over this period.",
    };
  }
  const series = data.tables[sourceId];
  const location = series.regions[region];
  const monthly = series.frequency === "monthly";
  const annual = monthly && frequency === "annual";
  const years = [...new Set(location.periods.map((date) => date.slice(0, 4)))];
  const fullYears = annual
    ? years.filter((year) =>
        Array.from(
          { length: 12 },
          (_, i) => year + "-" + String(i + 1).padStart(2, "0"),
        ).every((month) => location.periods.includes(month)),
      )
    : [];
  const periods = annual ? fullYears : location.periods;
  const items = {};
  for (const [id, item] of Object.entries(series.packages)) {
    const raw = Object.fromEntries(
      location.periods.map((date, index) => [
        date,
        location.values[id]?.[index] ?? null,
      ]),
    );
    const prices = annual
      ? Object.fromEntries(
          fullYears.map((year) => {
            const months = location.periods.filter((date) =>
              date.startsWith(year + "-"),
            );
            const values = months.map((date) => raw[date]);
            const mean = values.some((value) => value === null)
              ? null
              : values.reduce((sum, value) => sum + value, 0) / 12;
            return [year, mean];
          }),
        )
      : raw;
    items[id] = { ...item, prices, vector: location.vectors?.[id] };
  }
  return {
    region,
    periods,
    items,
    source: series.source,
    method: series.method,
  };
}
