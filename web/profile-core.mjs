// GeneRev4 web profile compatibility layer (Nico CSV / TXT formats).
// The browser preview never sends physical roaster commands.
export function parseProfile(source) {
  const text = String(source).replace(/\uFEFF/g, "");
  const lines = text.split(/\r?\n/).map(x => x.trim()).filter(x => x && !x.startsWith("#"));
  if (!lines.length) throw Error("Üres profilfájl.");
  let points = [];
  if (lines.some(x => /^\[[tT]\d+\s*=/.test(x))) {
    const times = new Map(), temps = new Map();
    const regex = /\[([tT])(\d+)\s*=\s*([+-]?\d+(?:[.,]\d+)?)\s*\]/g;
    for (const match of text.matchAll(regex)) {
      const id = Number(match[2]), value = Number(match[3].replace(",", "."));
      if (match[1] === "t") times.set(id, value);
      else temps.set(id, value);
    }
    if (!times.size || times.size !== temps.size || [...times.keys()].some(x => !temps.has(x))) {
      throw Error("Hibás TXT: minden [tN=...] időponthoz kell [TN=...] célhőmérséklet.");
    }
    points = [...times.keys()].sort((a,b) => a-b).map(id => ({time: times.get(id), temp: temps.get(id)}));
  } else {
    points = lines.filter(x => !/^999\s*;/.test(x)).map(line => {
      const cells = line.split(";");
      if (cells.length < 2) throw Error("Hibás CSV sor: " + line);
      return {time:Number(cells[0].trim()), temp:Number(cells[1].trim().replace(",", "."))};
    });
  }
  if (!points.length) throw Error("A profilban nincs idő–hőmérséklet pont.");
  if (points.length > 2000) throw Error("Túl sok profilpont (maximum 2000).");
  let last = -1;
  for (const p of points) {
    if (!Number.isInteger(p.time) || p.time < 0 || p.time > 21600 || p.time <= last) {
      throw Error("Az időpontok egész másodpercek, szigorúan növekvők és legfeljebb 6 órásak legyenek.");
    }
    if (!Number.isFinite(p.temp) || p.temp < 150 || p.temp > 250) {
      throw Error("A célhőmérsékletnek 150–250 °C között kell lennie.");
    }
    last = p.time;
  }
  return points;
}
export function targetAt(points, second) {
  if (!points.length || second < points[0].time) return null;
  let current = null;
  for (const p of points) { if (p.time > second) break; current = p.temp; }
  return current;
}
export function toCsv(points) {
  return "999;GeneRev4 web profile\r\n" + points.map(p => p.time + ";" + p.temp.toFixed(1)).join("\r\n") + "\r\n";
}
export function toTxt(points) {
  return points.map((p,i) => "[t" + (i+1) + "=" + p.time + "]\n[T" + (i+1) + "=" + p.temp.toFixed(1) + "]").join("\n") + "\n";
}
export function asClock(sec) {
  const n = Math.max(0, Math.floor(Number(sec) || 0));
  return String(Math.floor(n/60)).padStart(2,"0") + ":" + String(n%60).padStart(2,"0");
}
export const EXAMPLE = Object.freeze([
  {time:0,temp:180},{time:60,temp:190},{time:120,temp:205},
  {time:180,temp:220},{time:240,temp:230},{time:300,temp:225},{time:360,temp:210}
]);
