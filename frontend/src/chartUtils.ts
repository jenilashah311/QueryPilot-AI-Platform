/** Pick X = dimension, Y = measure from tabular result (handles column order from SQL). */
export function pickChartKeys(
  columns: string[],
  rows: Record<string, string | number | null | undefined>[],
): { xKey: string; yKey: string } {
  if (!columns.length || !rows.length) return { xKey: "", yKey: "" };

  const isNumeric = (v: unknown): boolean => {
    if (v === null || v === undefined) return false;
    if (typeof v === "number" && !Number.isNaN(v)) return true;
    if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) return true;
    return false;
  };

  const numericScore = (c: string): number => {
    const vals = rows.map((r) => r[c]).filter((v) => v !== null && v !== undefined);
    if (!vals.length) return -1;
    const numCount = vals.filter((v) => isNumeric(v)).length;
    let s = numCount / vals.length;
    // Prefer "count-ish" columns over generic averages when choosing measures.
    // This keeps charts/KPIs aligned with expectations like "how many HR ...".
    if (/count|row[_-]?count|total[_-]?count|num_|quantity|records|rows/i.test(c)) {
      s += 3;
    } else if (/revenue|amount|spend|clicks|conversions|total|sum|metric|score|n$/i.test(c)) {
      s += 2.25;
    } else if (/avg|mean|average/i.test(c)) {
      s += 1.25;
    }
    return s;
  };

  const sortedByY = [...columns].sort((a, b) => numericScore(b) - numericScore(a));
  const yKey = sortedByY[0] || columns[columns.length - 1];

  const sortedByDim = [...columns].sort((a, b) => numericScore(a) - numericScore(b));
  const isIdLike = (c: string): boolean => {
    const cl = c.toLowerCase();
    return cl === "id" || cl.endsWith("_id") || cl.endsWith(" id");
  };

  const dimPriority = [
    "region",
    "product_category",
    "category",
    "department",
    "channel",
    "issue_category",
    "warehouse",
    "inventory_category",
    "status",
    "priority",
    "job_level",
    "date",
  ];

  const dimCandidates = columns.filter((c) => c !== yKey && !isIdLike(c));

  const xKeyByPriority =
    dimPriority
      .map((p) => dimCandidates.find((c) => c.toLowerCase().includes(p)))
      .find(Boolean) || null;

  const xKey =
    xKeyByPriority ||
    sortedByDim.find((c) => c !== yKey && !isIdLike(c)) ||
    columns.find((c) => c !== yKey && !isIdLike(c)) ||
    sortedByDim.find((c) => c !== yKey) ||
    columns[0];

  return { xKey, yKey };
}

export function formatAxisNumber(n: number): string {
  if (!Number.isFinite(n)) return "";
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 10_000) return `${(n / 1_000).toFixed(2)}k`;
  if (abs >= 1000) return `${(n / 1000).toFixed(2)}k`;
  if (Number.isInteger(n)) return String(n);
  return n.toFixed(2);
}
