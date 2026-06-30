"""Quick deterministic-only comparison of the prompt templates.

Calls Gemma directly for each customer with each prompt template and checks the
hard next-purchase gate (the same logic as assert_next_match.py). Does NOT run the
OpenAI embedding/judge rubrics — it isolates the dominant signal so we can compare
prompts without an OpenAI key.
"""
import sys
import reco_common as rc
from recommend import call_gemma, clean, SYSTEM

PROMPTS = ["prompts/simple_recommender.txt", "prompts/advanced_recommender.txt"]


def render(path, vars):
    t = open(path, encoding="utf-8").read()
    for k, v in vars.items():
        t = t.replace("{{" + k + "}}", str(v))
    return t


def norm(s):
    return " ".join(str(s).lower().replace("–", "-").split())


def matches(out, expected):
    o, e = norm(out), norm(expected)
    return o == e or e in o or o in e


def main():
    products = rc.load_products()
    orders = rc.load_orders()
    rows = []
    for cid in sorted(orders.keys()):
        c = orders[cid]
        history, nxt = rc.split_history(c["items"])
        vars = {
            "history_text": rc.fmt_history(history, products),
            "catalogue_text": rc.fmt_catalogue(products),
            "avg_spend": rc.avg_spend(history),
            "today": rc.TODAY,
        }
        rows.append((cid, c["name"], nxt["product_name"], vars))

    score = {p: 0 for p in PROMPTS}
    for cid, name, want, vars in rows:
        line = f"{cid} {name:7s} want={want!r}"
        for p in PROMPTS:
            out = clean(call_gemma(SYSTEM, render(p, vars)))
            hit = matches(out, want)
            score[p] += hit
            tag = "simple" if "simple" in p else "advanced"
            line += f"\n   [{tag:8s}] {'HIT ' if hit else 'miss'} {out!r}"
        print(line)
    print("\n=== deterministic hit count ===")
    for p in PROMPTS:
        print(f"  {p}: {score[p]}/{len(rows)}")


if __name__ == "__main__":
    main()
