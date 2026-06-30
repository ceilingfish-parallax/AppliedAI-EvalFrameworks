"""Shared loaders/formatters for the recommendation eval.

Used by both recommend.py (the Gemma provider/CLI) and generate_tests.py so the
purchase history and catalogue are formatted identically everywhere.
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))  # CSVs live in the project root

TODAY = "2026-06-29"


def load_products():
    products = {}
    with open(os.path.join(ROOT, "products.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["price"] = float(r["price"])
            products[r["product_id"]] = r
    return products


def load_orders():
    """customer_id -> {name, items:[{product_id, product_name, order_date, unit_price}]} sorted by date."""
    cust = defaultdict(lambda: {"name": None, "items": []})
    with open(os.path.join(ROOT, "orders.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            c = cust[r["customer_id"]]
            c["name"] = r["customer_name"]
            c["items"].append({
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "order_date": r["order_date"],
                "unit_price": float(r["unit_price"]),
            })
    for c in cust.values():
        c["items"].sort(key=lambda x: x["order_date"])
    return cust


def load_top_recos():
    """customer_id -> (product_name, success_rate) with the highest success rate."""
    best = {}
    with open(os.path.join(ROOT, "successful_recommendations.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rate = float(r["success_rate"])
            cid = r["customer_id"]
            if cid not in best or rate > best[cid][1]:
                best[cid] = (r["recommended_product"], rate)
    return best


def fmt_catalogue(products):
    lines = []
    for p in products.values():
        lines.append(f"- {p['name']} | {p['category']} | £{p['price']:.0f} | released {p['release_date']}")
    return "\n".join(lines)


def fmt_history(items, products):
    lines = []
    for it in items:
        p = products[it["product_id"]]
        lines.append(f"- {it['product_name']} ({p['category']}, £{p['price']:.0f}) — bought {it['order_date']}")
    return "\n".join(lines)


def avg_spend(items):
    return round(sum(it["unit_price"] for it in items) / len(items)) if items else 0


def split_history(items):
    """All purchases except the most recent (=history), and the most recent (=held-out next)."""
    return items[:-1], items[-1]
