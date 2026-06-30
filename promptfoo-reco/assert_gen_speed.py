"""Deterministic speed scorer: how fast did the engine generate, relative to 60s?

Continuous score on [0, 1]:
    score = 1 - (gen_seconds / 60)
A 1s generation scores 1 - 1/60 (~0.983); a 60s (or slower) generation scores 0.
No model involved — pure arithmetic on the wall-clock time the provider measured.

Generation time comes from recommend.py, which stamps it onto the provider
response metadata as `gen_seconds`. We fall back to promptfoo's own latencyMs
(the full provider round-trip) if the metadata is missing.
"""

BUDGET_SECONDS = 60.0


def _gen_seconds(context):
    # Preferred: the time recommend.py measured around the LM Studio call.
    meta = context.get("metadata") or {}
    if meta.get("gen_seconds") is not None:
        return float(meta["gen_seconds"])

    pr = context.get("providerResponse") or {}
    pr_meta = pr.get("metadata") or {}
    if pr_meta.get("gen_seconds") is not None:
        return float(pr_meta["gen_seconds"])

    # Fallback: promptfoo's measured latency for the whole provider call.
    if pr.get("latencyMs") is not None:
        return float(pr["latencyMs"]) / 1000.0
    return None


def get_assert(output, context):
    gen = _gen_seconds(context)
    if gen is None:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "No generation time available (no gen_seconds metadata or latencyMs).",
        }

    score = max(0.0, 1.0 - gen / BUDGET_SECONDS)
    return {
        "pass": gen < BUDGET_SECONDS,
        "score": score,
        "reason": f"Generated in {gen:.2f}s -> score {score:.3f} (1 - {gen:.2f}/{BUDGET_SECONDS:.0f}).",
    }
