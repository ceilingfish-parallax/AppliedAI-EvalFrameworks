"""Deterministic scorer: did the recommendation match what the customer bought next?

The hardest, cleanest signal — pure string comparison against the held-out purchase,
no model involved. Pass if the recommended product is (or clearly contains) the actual
next product.
"""


def _norm(s):
    return " ".join(str(s).lower().replace("–", "-").split())


def get_assert(output, context):
    expected = context["vars"]["next_product"]
    o, e = _norm(output), _norm(expected)
    match = o == e or e in o or o in e
    return {
        "pass": match,
        "score": 1.0 if match else 0.0,
        "reason": (f"Recommended the actual next purchase ({expected})."
                   if match else
                   f"Recommended {output!r}; customer actually bought {expected!r} next."),
    }
