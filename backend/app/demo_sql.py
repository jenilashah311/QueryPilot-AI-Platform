"""Rule-based SQL for DEMO_MODE when no LLM key is configured — avoids grouping by arbitrary first columns (e.g. order_id)."""
from __future__ import annotations

import re
from typing import Any


def _q(c: str) -> str:
    return f'"{c}"'

def _lit(v: Any) -> str:
    # Simple SQL literal escaping for demo-rule generation.
    # Values come from CSV-distinct queries, so they should be treated as strings.
    s = "" if v is None else str(v)
    return "'" + s.replace("'", "''") + "'"


def _col(cols: list[str], *needles: str) -> str | None:
    for n in needles:
        for c in cols:
            if n in c.lower():
                return c
    return None


def _skip_id_dimension(cols: list[str]) -> list[str]:
    out = []
    for c in cols:
        cl = c.lower()
        if re.search(r"^(?:.*_)?id$", cl) and cl not in ("grid", "paid"):
            continue
        out.append(c)
    return out or cols


def _pick_dimension(cols: list[str]) -> str:
    priority = (
        "region",
        "product_category",
        "department",
        "channel",
        "issue_category",
        "warehouse",
        "inventory_category",
        "status",
        "priority",
        "job_level",
    )
    for p in priority:
        for c in cols:
            if p in c.lower():
                return c
    candidates = _skip_id_dimension(cols)
    return candidates[0] if candidates else cols[0]


def _pick_measure(cols: list[str], dim: str) -> str | None:
    for c in cols:
        if c == dim:
            continue
        cl = c.lower()
        if any(
            x in cl
            for x in (
                "revenue",
                "salary",
                "quantity",
                "amount",
                "spend",
                "clicks",
                "impressions",
                "conversions",
                "score",
                "cost",
                "minutes",
            )
        ):
            return c
    return None


def build_demo_sql(
    schema: str,
    cols: list[str],
    question: str,
    *,
    dept_values: list[str] | None = None,
    job_values: list[str] | None = None,
) -> str:
    if not cols:
        raise ValueError("No columns")
    t = f'{_q(schema)}.{_q("analytics_primary")}'
    q = question.lower()

    # Global filter extraction for demo queries:
    # - Find likely department/job_level columns by name
    # - Match any distinct value that appears in the question (no CSV-specific hardcoding).
    dept_col = _col(cols, "department", "dept")
    job_col = _col(cols, "job_level", "joblevel", "level")

    where: list[str] = []
    if dept_col and dept_values:
        ql = q
        for dv in dept_values:
            if dv is None:
                continue
            dl = str(dv).strip().lower()
            if not dl:
                continue
            if dl in ql:
                where.append(f"{_q(dept_col)} = {_lit(dv)}")
                break

    if job_col and job_values:
        ql = q
        for jv in job_values:
            if jv is None:
                continue
            jl = str(jv).strip().lower()
            if not jl:
                continue
            if jl in ql:
                where.append(f"{_q(job_col)} = {_lit(jv)}")
                break

    where_sql = f" WHERE {' AND '.join(where)}" if where else ""

    if any(
        ph in q
        for ph in (
            "how many row",
            "how many rows",
            "number of row",
            "number of rows",
            "count the row",
            "count rows",
            "how many records",
        )
    ):
        return f"SELECT COUNT(*)::bigint AS row_count FROM {t}{where_sql}"

    if ("how many" in q or ("count" in q and "group" not in q)) and "group" not in q and " by " not in q:
        if "distinct" in q:
            d = _pick_dimension(cols)
            return f"SELECT COUNT(DISTINCT {_q(d)})::bigint AS distinct_{d} FROM {t}{where_sql}"
        return f"SELECT COUNT(*)::bigint AS row_count FROM {t}{where_sql}"

    region = _col(cols, "region", "territory")
    revenue = _col(cols, "revenue", "sales_amount", "amount")
    qty = _col(cols, "quantity", "qty", "units")
    cat = _col(cols, "product_category", "category", "inventory_category")

    if ("revenue" in q or ("total" in q and "sales" in q)) and "region" in q:
        if region and revenue:
            return (
                f"SELECT {_q(region)} AS region, SUM({_q(revenue)})::double precision AS total_revenue "
                f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST"
            )
        if region and qty:
            return (
                f"SELECT {_q(region)} AS region, SUM({_q(qty)})::double precision AS total_quantity "
                f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST"
            )

    if "revenue" in q and ("total" in q or "sum" in q or "by" in q):
        if cat and revenue:
            return (
                f"SELECT {_q(cat)} AS category, SUM({_q(revenue)})::double precision AS total_revenue "
                f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST"
            )
        if region and revenue:
            return (
                f"SELECT {_q(region)} AS region, SUM({_q(revenue)})::double precision AS total_revenue "
                f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST"
            )

    dept = _col(cols, "department", "dept")
    sal = _col(cols, "salary", "compensation", "annual_salary")
    if ("salary" in q or "compensation" in q) and ("department" in q or "dept" in q or "by" in q):
        if dept and sal:
            agg = "AVG" if "average" in q or "avg" in q else "SUM"
            return (
                f"SELECT {_q(dept)} AS department, {agg}({_q(sal)})::double precision AS salary_metric "
                f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST"
            )

    channel = _col(cols, "channel")
    conv = _col(cols, "conversion")
    spend = _col(cols, "spend")
    if "channel" in q and conv:
        return (
            f"SELECT {_q(channel)} AS channel, SUM({_q(conv)})::double precision AS total_conversions "
            f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST"
        )
    if "channel" in q and spend and ("spend" in q or "cost" in q):
        return (
            f"SELECT {_q(channel)} AS channel, SUM({_q(spend)})::double precision AS total_spend "
            f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST"
        )

    issue = _col(cols, "issue_category")
    if issue and ("ticket" in q or "support" in q):
        return (
            f"SELECT {_q(issue)} AS issue_category, COUNT(*)::bigint AS ticket_count "
            f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST LIMIT 50"
        )

    dim = _pick_dimension(cols)
    meas = _pick_measure(cols, dim)
    if meas:
        if "average" in q or "avg" in q or "mean" in q:
            return (
                f"SELECT {_q(dim)} AS bucket, AVG({_q(meas)})::double precision AS avg_metric "
                f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST LIMIT 50"
            )
        return (
            f"SELECT {_q(dim)} AS bucket, SUM({_q(meas)})::double precision AS sum_metric "
            f"FROM {t} GROUP BY 1 ORDER BY 2 DESC NULLS LAST LIMIT 50"
        )

    c0 = cols[0]
    return f'SELECT {_q(c0)}, COUNT(*)::bigint AS n FROM {t} GROUP BY 1 ORDER BY n DESC LIMIT 20'


def demo_insight(rows: list[dict[str, Any]], question: str) -> str:
    n = len(rows)
    return (
        f"Demo mode (rule-based SQL): returned {n} row(s). "
        "For natural phrasing + smarter SQL + summaries, set OPENAI_API_KEY (e.g. OpenRouter), "
        "OPENAI_BASE_URL if needed, OPENAI_MODEL, and DEMO_MODE=false."
    )
