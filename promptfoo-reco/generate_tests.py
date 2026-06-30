"""Generate one promptfoo test per customer.

For each customer we hold out their most recent purchase as the ground-truth
"what they bought next", and expose everything the prompt and the three scorers need.
"""
import reco_common as rc


def generate_tests():
    products = rc.load_products()
    orders = rc.load_orders()
    top_recos = rc.load_top_recos()

    tests = []
    for cid in sorted(orders.keys()):
        c = orders[cid]
        history, nxt = rc.split_history(c["items"])
        top_reco = top_recos.get(cid, ("", 0.0))

        tests.append({
            "vars": {
                "customer_id": cid,
                "customer_name": c["name"],
                "history_text": rc.fmt_history(history, products),
                "catalogue_text": rc.fmt_catalogue(products),
                "avg_spend": rc.avg_spend(history),
                "today": rc.TODAY,
                "next_product": nxt["product_name"],        # deterministic target
                "top_reco": top_reco[0],                    # similarity reference
                "top_reco_success": top_reco[1],
            },
            "description": f'{c["name"]} ({cid})',
        })
    return tests


if __name__ == "__main__":
    t = generate_tests()
    print(f"{len(t)} customer test cases")
    v = t[0]["vars"]
    print("vars:", list(v.keys()))
    print("example next_product:", v["next_product"], "| top_reco:", v["top_reco"])
