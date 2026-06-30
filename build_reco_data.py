"""Build the product-recommendation dataset for the eval demo.

Writes three CSVs (the source of truth for the talk):

  products.csv                  - everything the shop sells (price + release_date)
  orders.csv                    - customer purchase histories, one row per purchase,
                                  chronological. The LAST purchase per customer is the
                                  held-out "what they bought next" (the deterministic target).
  successful_recommendations.csv- recommendations from a NON-LLM engine, with the
                                  relative success rate of each. The highest success rate
                                  per customer is the reference for the similarity scorer.

A coffee-equipment shop: clear complements, real price tiers, and a few 2026 lines so
"recency" is a meaningful axis.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# product_id: (name, category, price, release_date)
PRODUCTS = {
    "P01": ("Cafetière (French Press)", "brewing", 22, "2023-02-01"),
    "P02": ("AeroPress Go", "brewing", 30, "2024-05-01"),
    "P03": ("V60 Pour-Over Dripper", "brewing", 25, "2023-09-01"),
    "P04": ("V60 Paper Filters (100)", "consumable", 6, "2022-01-01"),
    "P05": ("Gooseneck Kettle", "equipment", 55, "2024-03-01"),
    "P06": ("Burr Grinder Classic", "grinder", 120, "2023-06-01"),
    "P07": ("Hand Grinder", "grinder", 45, "2024-08-01"),
    "P08": ("Espresso Machine Mini", "espresso", 450, "2024-11-01"),
    "P09": ("Milk Frother", "espresso", 25, "2023-04-01"),
    "P10": ("Coffee Beans – House Blend (1kg)", "beans", 18, "2025-01-01"),
    "P11": ("Coffee Beans – Single Origin (250g)", "beans", 9, "2025-01-01"),
    "P12": ("Brewing Scales", "accessory", 30, "2024-02-01"),
    "P13": ("Ceramic Mug Set (x4)", "accessory", 28, "2023-12-01"),
    "P14": ("Travel Cup", "accessory", 16, "2024-06-01"),
    "P15": ("Descaler Solution", "consumable", 8, "2022-07-01"),
    "P16": ("Storage Canister", "accessory", 19, "2025-03-01"),
    "P17": ("V60 Pro Dripper (2026)", "brewing", 35, "2026-04-01"),
    "P18": ("Burr Grinder X2 (2026)", "grinder", 160, "2026-05-01"),
    "P19": ("Smart Scales (2026)", "accessory", 48, "2026-03-01"),
}

# customer_id: (name, [ (product_id, order_date) ... chronological; LAST = held-out next ])
CUSTOMERS = {
    "C001": ("Ella", [("P03", "2023-10-05"), ("P04", "2023-11-02"),
                       ("P05", "2024-01-15"), ("P11", "2024-03-10")]),
    "C002": ("Marcus", [("P08", "2024-12-01"), ("P09", "2025-01-10"),
                        ("P15", "2025-02-20"), ("P06", "2025-04-05")]),
    "C003": ("Priya", [("P01", "2024-03-03"), ("P10", "2024-04-01"),
                       ("P13", "2024-06-12")]),
    "C004": ("Tom", [("P02", "2025-09-09"), ("P11", "2025-11-01")]),
    "C005": ("Sara", [("P12", "2024-02-14"), ("P16", "2025-03-20"),
                      ("P19", "2026-05-15")]),
    "C006": ("Dan", [("P06", "2023-07-01"), ("P10", "2023-08-01"),
                     ("P11", "2023-10-01"), ("P18", "2026-05-20")]),
    "C007": ("Nina", [("P03", "2024-09-01"), ("P04", "2024-10-01"),
                      ("P17", "2026-04-15")]),
    "C008": ("Raj", [("P13", "2025-01-05"), ("P14", "2025-02-05"),
                     ("P10", "2025-04-01")]),
    "C009": ("Helen", [("P05", "2024-05-01"), ("P12", "2024-06-01"),
                       ("P03", "2024-07-01"), ("P04", "2024-09-01")]),
    "C010": ("Omar", [("P08", "2025-03-01"), ("P09", "2025-05-01")]),
}

# customer_id: [ (product_id, success_rate) ... ] from the non-LLM engine.
# Highest success_rate = the reference recommendation for the similarity scorer.
RECOS = {
    "C001": [("P12", 0.62), ("P11", 0.58)],
    "C002": [("P06", 0.71), ("P07", 0.40)],
    "C003": [("P13", 0.54), ("P14", 0.42)],
    "C004": [("P11", 0.66), ("P10", 0.50)],
    "C005": [("P13", 0.48), ("P19", 0.39)],
    "C006": [("P10", 0.60), ("P18", 0.45)],
    "C007": [("P04", 0.64), ("P17", 0.50)],
    "C008": [("P10", 0.57), ("P11", 0.49)],
    "C009": [("P04", 0.69), ("P13", 0.41)],
    "C010": [("P09", 0.66), ("P06", 0.52)],
}


def main():
    with open(os.path.join(HERE, "products.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "name", "category", "price", "release_date"])
        for pid, (name, cat, price, rel) in PRODUCTS.items():
            w.writerow([pid, name, cat, price, rel])

    with open(os.path.join(HERE, "orders.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer_id", "customer_name", "product_id",
                    "product_name", "order_date", "unit_price"])
        oid = 1000
        for cid, (cname, hist) in CUSTOMERS.items():
            for pid, date in hist:
                oid += 1
                name, _, price, _ = PRODUCTS[pid]
                w.writerow([f"O{oid}", cid, cname, pid, name, date, price])

    with open(os.path.join(HERE, "successful_recommendations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "customer_name", "recommended_product_id",
                    "recommended_product", "success_rate"])
        for cid, recos in RECOS.items():
            cname = CUSTOMERS[cid][0]
            for pid, rate in sorted(recos, key=lambda r: -r[1]):
                w.writerow([cid, cname, pid, PRODUCTS[pid][0], rate])

    n_orders = sum(len(h) for _, h in CUSTOMERS.values())
    print(f"products: {len(PRODUCTS)} | customers: {len(CUSTOMERS)} | order rows: {n_orders}")
    print("held-out 'next purchase' per customer:")
    for cid, (cname, hist) in CUSTOMERS.items():
        nxt = PRODUCTS[hist[-1][0]][0]
        top = max(RECOS[cid], key=lambda r: r[1])
        flag = "ENGINE HIT" if top[0] == hist[-1][0] else "engine misses"
        print(f"  {cid} {cname:7} next={nxt:38} | top reco={PRODUCTS[top[0]][0]:38} [{flag}]")


if __name__ == "__main__":
    main()
