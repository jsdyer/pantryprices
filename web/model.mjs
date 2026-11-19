export function basket(items, quantities, year) {
  const lines = Object.entries(items)
    .filter(([key]) => quantities[key] > 0)
    .map(([key, item]) => {
      const unitCents = item.prices[year];
      return {
        key,
        label: item.label,
        unit: item.unit,
        page: item.page,
        quantity: quantities[key],
        unitCents,
        costCents: quantities[key] * unitCents,
      };
    });
  return { lines, total: lines.reduce((sum, line) => sum + line.costCents, 0) };
}
