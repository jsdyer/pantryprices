import { compare, seriesFor } from "./coffee.mjs";

const id = name => document.getElementById("coffee-" + name);
const fmt = new Intl.NumberFormat("en-CA", { maximumFractionDigits: 1, minimumFractionDigits: 1, signDisplay: "exceptZero" });
const pct = value => value === null ? "Unavailable" : fmt.format(value) + "%";
const price = value => value === null ? "—" : value.toFixed(2);
const svgNS = "http://www.w3.org/2000/svg";

function node(tag, text, parent) {
  const el = document.createElement(tag);
  el.textContent = text;
  parent.append(el);
  return el;
}

function svg(tag, attrs, parent) {
  const el = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  parent.append(el);
  return el;
}

function draw(points, series) {
  const chart = id("chart");
  chart.replaceChildren();
  const values = points.flatMap(p => Object.values(p.changes).filter(v => v !== null));
  const lower = Math.floor(Math.min(0, ...values) / 10) * 10;
  const upper = Math.max(lower + 10, Math.ceil(Math.max(0, ...values) / 10) * 10);
  const x = i => 65 + 615 * i / Math.max(1, points.length - 1);
  const y = value => 195 - 170 * (value - lower) / (upper - lower);
  const axis = [...new Set([lower, 0, upper])];
  for (const value of axis) {
    svg("line", { x1: 65, x2: 680, y1: y(value), y2: y(value), stroke: value === 0 ? "#77827e" : "#d5dada" }, chart);
    svg("text", { x: 57, y: y(value) + 5, "text-anchor": "end" }, chart).textContent = value + "%";
  }
  for (const { key, colour, dash } of series) {
    let path = "";
    let connected = false;
    for (const [i, { changes }] of points.entries()) {
      const value = changes[key];
      if (value === null) { connected = false; continue; }
      path += (connected ? "L" : "M") + x(i) + "," + y(value) + " ";
      // An isolated observation still needs a visible mark.
      if (!connected && points[i + 1]?.changes[key] == null) {
        svg("circle", { cx: x(i), cy: y(value), r: 3, fill: colour }, chart);
      }
      connected = true;
    }
    svg("path", { d: path, stroke: colour, "stroke-width": 3, "stroke-dasharray": dash, fill: "none" }, chart);
  }
  svg("text", { x: 65, y: 222 }, chart).textContent = points[0].row.month;
  if (points.length > 1) svg("text", { x: 680, y: 222, "text-anchor": "end" }, chart).textContent = points.at(-1).row.month;
}

function render(edition, series) {
  const { rows } = edition;
  const start = id("start").value;
  const end = id("end").value;
  const threshold = Number(id("threshold").value);
  const { points, crossings } = compare(rows, start, end, threshold, series);
  draw(points, series);
  id("chart").setAttribute("aria-label", "Monthly percentage changes since " + start + ". Values are in the table below.");
  id("legend").replaceChildren();
  for (const { name } of series) node("span", name, id("legend"));
  for (const [index, label] of ["first", "second"].entries()) {
    id(label + "-price").textContent = series[index + 1].name + " C$/340 g";
    id(label + "-change").textContent = series[index + 1].name + " change";
  }
  const last = points.at(-1).changes;
  id("result").textContent = "From " + start + " to " + end + " · " + series.map(s => s.name + " " + pct(last[s.key])).join(" · ");
  const events = id("events");
  events.replaceChildren();
  for (const { key, name } of series) {
    const index = crossings[key];
    let detail = "threshold not reached in the published months";
    if (index !== null) {
      detail = points[index].row.month;
      if (key !== "cad" && crossings.cad !== null) {
        const delta = index - crossings.cad;
        detail += delta === 0 ? " · same month as the benchmark" :
          " · " + Math.abs(delta) + (Math.abs(delta) === 1 ? " month " : " months ") + (delta > 0 ? "after" : "before") + " the benchmark";
      }
    }
    node("li", name + " · " + detail, events);
  }
  const body = id("rows");
  body.replaceChildren();
  for (const { row, changes } of points) {
    const tr = node("tr", "", body);
    node("th", row.month, tr).scope = "row";
    for (const value of [price(row.usd), row.fx?.toFixed(4) ?? "—", price(row.cad), ...series.slice(1).map(({key}) => price(row[key])),
                         ...series.map(s => pct(changes[s.key]))]) node("td", value, tr);
  }
}

async function load() {
  const response = await fetch("./data/coffee.json");
  if (!response.ok) throw new Error("Coffee dataset is unavailable.");
  const edition = await response.json();
  const regions = edition.regions ?? [{ key: "bc", name: "British Columbia" }, { key: "ns", name: "Nova Scotia" }];
  const first = id("first"), second = id("second"), start = id("start"), end = id("end");
  for (const region of [...regions].sort((a, b) => a.name.localeCompare(b.name))) {
    first.add(new Option(region.name, region.key));
    second.add(new Option(region.name, region.key));
  }
  const requested = new URLSearchParams(location.search).get("coffeeProvince");
  first.value = regions.some(r => r.key === requested) ? requested : "bc";
  second.value = first.value === "ns" ? "bc" : "ns";
  for (const row of edition.rows) end.add(new Option(row.month, row.month));
  end.value = edition.end;
  let selectedSeries;
  function update() {
    for (const option of end.options) option.disabled = option.value < start.value;
    if (end.value < start.value) end.value = start.value;
    render(edition, selectedSeries);
  }
  function changeRegions() {
    for (const option of first.options) option.disabled = option.value === second.value;
    for (const option of second.options) option.disabled = option.value === first.value;
    selectedSeries = seriesFor(regions.find(r => r.key === first.value), regions.find(r => r.key === second.value));
    const complete = edition.rows.filter(row => selectedSeries.every(({ key }) => row[key] > 0));
    const oldStart = start.value;
    start.replaceChildren();
    for (const row of complete) start.add(new Option(row.month, row.month));
    if (!complete.length) {
      id("chart").replaceChildren();
      id("legend").replaceChildren();
      id("rows").replaceChildren();
      id("events").replaceChildren();
      id("result").textContent = "These provinces have no shared base month. Choose another pair.";
      return;
    }
    start.value = complete.some(row => row.month === oldStart) ? oldStart : complete[Math.max(0, complete.length - 36)].month;
    update();
  }
  for (const el of [first, second]) el.addEventListener("change", changeRegions);
  for (const el of [start, end, id("threshold")]) el.addEventListener("change", () => {
    if (start.value) update();
  });
  id("controls").disabled = false;
  id("edition").textContent = edition.start + " to " + edition.end + " · " + edition.rows.length +
    " calendar months · Sources retrieved " + edition.retrieved + " UTC";
  changeRegions();
}
load().catch(() => {
  id("edition").textContent = "The coffee comparison could not load. The full CSV is linked below.";
});
