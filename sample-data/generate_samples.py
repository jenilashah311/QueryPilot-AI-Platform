#!/usr/bin/env python3
"""Generate 5 category-diverse sample CSVs (100–300 rows) for analytics / Text-to-SQL demos."""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

RNG = random.Random(42)
OUT = Path(__file__).parent


def daterange(n: int, end: date | None = None) -> list[date]:
    end = end or date(2025, 12, 31)
    start = end - timedelta(days=n * 2)
    return [start + timedelta(days=RNG.randint(0, (end - start).days)) for _ in range(n)]


def write_sales(n: int = 180) -> None:
    cats = ["Electronics", "Apparel", "Home", "Sports", "Books", "Beauty"]
    regions = ["North", "South", "East", "West", "Central"]
    rows = []
    for i in range(1, n + 1):
        rows.append(
            {
                "order_id": f"ORD-{i:05d}",
                "order_date": daterange(1)[0].isoformat(),
                "product_category": RNG.choice(cats),
                "region": RNG.choice(regions),
                "quantity": RNG.randint(1, 12),
                "revenue_usd": round(RNG.uniform(15.0, 899.0), 2),
            }
        )
    _write("01_retail_sales_orders.csv", rows)


def write_hr(n: int = 220) -> None:
    depts = ["Engineering", "Sales", "Marketing", "Ops", "Finance", "HR", "Legal"]
    titles = ["IC", "Senior IC", "Lead", "Manager", "Director"]
    rows = []
    base = date(2018, 1, 1)
    for i in range(1, n + 1):
        hire = base + timedelta(days=RNG.randint(0, 2500))
        rows.append(
            {
                "employee_id": f"E{i:04d}",
                "department": RNG.choice(depts),
                "job_level": RNG.choice(titles),
                "hire_date": hire.isoformat(),
                "annual_salary_usd": RNG.randrange(52000, 195000, 1000),
                "performance_score": round(RNG.uniform(2.5, 5.0), 1),
            }
        )
    _write("02_hr_employees.csv", rows)


def write_marketing(n: int = 250) -> None:
    channels = ["Email", "Social", "Search", "Display", "Partner", "Video"]
    rows = []
    for i in range(1, n + 1):
        imp = RNG.randint(5000, 500000)
        ctr = RNG.uniform(0.008, 0.045)
        clicks = max(1, int(imp * ctr))
        conv_rate = RNG.uniform(0.02, 0.18)
        conv = max(0, int(clicks * conv_rate))
        spend = round(RNG.uniform(200.0, 12000.0), 2)
        rows.append(
            {
                "campaign_id": f"CMP-{i:04d}",
                "channel": RNG.choice(channels),
                "date": daterange(1)[0].isoformat(),
                "impressions": imp,
                "clicks": clicks,
                "conversions": conv,
                "spend_usd": spend,
            }
        )
    _write("03_marketing_campaigns.csv", rows)


def write_inventory(n: int = 150) -> None:
    wh = ["WH-East", "WH-West", "WH-Central", "WH-South"]
    cat = ["Raw", "WIP", "Finished", "Spare Parts", "Packaging"]
    rows = []
    for i in range(1, n + 1):
        uoh = RNG.randint(0, 5000)
        rows.append(
            {
                "sku": f"SKU-{RNG.choice('ABCDEFGH')}{i:05d}",
                "warehouse": RNG.choice(wh),
                "inventory_category": RNG.choice(cat),
                "units_on_hand": uoh,
                "reorder_point": RNG.randint(50, 800),
                "unit_cost_usd": round(RNG.uniform(2.5, 450.0), 2),
            }
        )
    _write("04_supply_chain_inventory.csv", rows)


def write_support(n: int = 280) -> None:
    cats = ["Billing", "Bug", "Account", "Shipping", "How-to", "Integration", "Other"]
    pri = ["P1", "P2", "P3", "P4"]
    stat = ["Open", "Pending", "Resolved", "Closed"]
    rows = []
    for i in range(1, n + 1):
        mins = RNG.randint(5, 4800) if RNG.random() > 0.08 else ""
        rows.append(
            {
                "ticket_id": f"TKT-{i:05d}",
                "created_date": daterange(1)[0].isoformat(),
                "issue_category": RNG.choice(cats),
                "priority": RNG.choice(pri),
                "status": RNG.choice(stat),
                "resolution_minutes": mins,
            }
        )
    _write("05_customer_support_tickets.csv", rows)


def _write(name: str, rows: list[dict]) -> None:
    if not rows:
        return
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {path} ({len(rows)} rows)")


def main() -> None:
    write_sales(180)
    write_hr(220)
    write_marketing(250)
    write_inventory(150)
    write_support(280)


if __name__ == "__main__":
    main()
