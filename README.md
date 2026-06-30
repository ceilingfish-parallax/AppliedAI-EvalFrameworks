# Recommendation eval — three scorers on one task

A coffee-equipment shop wants to recommend each customer's next product. A **local Gemma**
model (in LM Studio) generates the recommendation; promptfoo scores it three ways — one of
each kind — so you can show on stage exactly what each technique can and can't see.

## The data (in the project root)

- `products.csv` — the catalogue: name, category, price, release_date.
- `orders.csv` — purchase histories, one row per purchase, chronological. The **most recent**
  purchase per customer is held out as "what they bought next" (the deterministic target).
- `successful_recommendations.csv` — recommendations from the shop's existing **non-LLM**
  engine, with a success rate each. The highest per customer is the similarity reference.

Regenerate them with `python ../build_reco_data.py`.

## The three scorers

| # | Scorer | Type | What it checks | Model used |
|---|--------|------|----------------|------------|
| 1 | `assert_next_match.py` | deterministic | Did Gemma recommend the product they actually bought next? | none (code) |
| 2 | `similar` | statistical | Embedding distance to the engine's most successful reco | OpenAI embeddings |
| 3 | `llm-rubric` ×3 | LLM-as-judge | Relevance, Affordability, Recency | OpenAI gpt-4o-mini |

## Setup

1. **LM Studio**: load a Gemma model and start the local server (Developer ▸ Start Server)
   so it's listening on `http://127.0.0.1:1234`. Override with `LMSTUDIO_URL` /
   `LMSTUDIO_MODEL` if yours differs.
2. **OpenAI key** (for the embeddings + judge only):
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

## Run

```bash
cd promptfoo-reco
npx promptfoo@latest eval
npx promptfoo@latest view
```

Try the generator on its own first to confirm Gemma is reachable:

```bash
python recommend.py --customer C006
```

## What each scorer reveals (the talk)

- **Deterministic is brutally honest but narrow.** It only rewards the *exact* next purchase.
  A genuinely good recommendation that isn't literally what they bought next scores 0 — which
  is the point: it's precise but it can't recognise a different good answer.
- **Similarity rewards agreeing with the old engine.** It measures closeness to the proven
  recommendation, not correctness. Useful as a sanity check, but it will mark *down* a smart
  new suggestion the legacy engine never made — note that every "engine misses" customer in
  the data is a 2026 product the old engine under-weights.
- **The judge sees the qualities that matter.** Relevance, affordability and recency are
  exactly the things code and embeddings can't read. This is also where you show the judge's
  own weaknesses — run it twice, tweak a rubric, show a verdict move — and make the point that
  you validate the judge against human labels.

The tension between the three is the lesson: deterministic says "wrong" while the judge says
"actually that's a better recommendation than what they bought." That disagreement is the
most interesting slide in the section.

## Notes

- Gemma is non-deterministic by default; set its temperature low in LM Studio (or accept the
  variation — it's a nice live illustration of exactly the problem the talk opens with).
- Costs: 10 customers × (1 embedding + 3 judge calls) per run — pennies on gpt-4o-mini.
- Swap the generator for any local/hosted model by changing the provider; the scorers don't care.
