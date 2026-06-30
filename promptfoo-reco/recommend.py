"""The recommendation engine under test: a local Gemma model in LM Studio.

Two ways to use it:

1. As a promptfoo provider (how the eval runs it):
       providers:
         - id: file://recommend.py
   promptfoo renders prompts/recommend.txt and calls `call_api(prompt, options, context)`.

2. As a standalone CLI (for ad-hoc tries / the live demo):
       python recommend.py --customer C001

Both hit LM Studio's OpenAI-compatible endpoint. Defaults assume LM Studio's default:
   http://127.0.0.1:1234/v1/chat/completions
Override with env vars LMSTUDIO_URL and LMSTUDIO_MODEL if needed.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

import reco_common as rc

LMSTUDIO_URL = os.environ.get("LMSTUDIO_URL", "http://127.0.0.1:1234/v1/chat/completions")
LMSTUDIO_MODEL = os.environ.get("LMSTUDIO_MODEL", "gemma")
# Default temperature for generation; CI sets RECO_TEMPERATURE=0 for determinism.
RECO_TEMPERATURE = float(os.environ.get("RECO_TEMPERATURE", "0.3"))

SYSTEM = ("You are a product recommendation engine for a coffee-equipment shop. "
          "Recommend exactly one product from the catalogue you are given. "
          "Reply with ONLY the exact product name, nothing else.")


def call_gemma(system, user, temperature=RECO_TEMPERATURE):
    payload = {
        "model": LMSTUDIO_MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    req = urllib.request.Request(
        LMSTUDIO_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def clean(text):
    """Keep just the product name: first non-empty line, stripped of quotes/bullets."""
    for line in text.splitlines():
        line = line.strip().strip('"').strip("'").lstrip("-•* ").strip()
        if line:
            return line
    return text.strip()


# ---- promptfoo provider entrypoint --------------------------------------
def call_api(prompt, options, context):
    try:
        t0 = time.perf_counter()
        raw = call_gemma(SYSTEM, prompt)
        gen_seconds = time.perf_counter() - t0
        # Surface generation time so a deterministic assertion can score speed.
        return {"output": clean(raw), "metadata": {"gen_seconds": gen_seconds}}
    except urllib.error.URLError as e:
        return {"error": f"Could not reach LM Studio at {LMSTUDIO_URL} — is it running? ({e})"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"Gemma call failed: {e}"}


# ---- CLI ----------------------------------------------------------------
def render_prompt(history_text, catalogue_text):
    tmpl_path = os.path.join(rc.HERE, "prompts", "recommend.txt")
    tmpl = open(tmpl_path, encoding="utf-8").read()
    return tmpl.replace("{{history_text}}", history_text).replace("{{catalogue_text}}", catalogue_text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--customer", required=True, help="customer id, e.g. C001")
    args = ap.parse_args()

    products = rc.load_products()
    orders = rc.load_orders()
    if args.customer not in orders:
        sys.exit(f"unknown customer {args.customer}")

    history, nxt = rc.split_history(orders[args.customer]["items"])
    prompt = render_prompt(rc.fmt_history(history, products), rc.fmt_catalogue(products))
    print(f"== {args.customer} {orders[args.customer]['name']} ==")
    print(f"(actually bought next: {nxt['product_name']})\n")
    print("Gemma recommends:", clean(call_gemma(SYSTEM, prompt)))


if __name__ == "__main__":
    main()
