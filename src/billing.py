"""
Billing module for Japan Market MCP — free→paid funnel (Gumroad).

Provides session-level call counter and billing metadata
for tool responses.
"""

FREE_SAMPLE = "https://atushi5.gumroad.com/l/kutuxe"
PRO_DATASET = "https://atushi5.gumroad.com/l/agyhq"
FREE_CALLS_PER_SESSION = 12

# Session-level counter (per process / per session)
_call_count = 0


def billing_meta() -> dict:
    """Return billing metadata for the current call and increment the counter.

    Returns:
        dict with tier, calls_used, free_limit, weekly_dataset, free_sample
    """
    global _call_count
    _call_count += 1
    return {
        "tier": "free",
        "calls_used": _call_count,
        "free_limit": FREE_CALLS_PER_SESSION,
        "weekly_dataset": PRO_DATASET,
        "free_sample": FREE_SAMPLE,
    }


def billing_text() -> str:
    """Return the billing footer text for str-type tool responses."""
    return (
        "[PR] Free tier: up to 12 calls per session. "
        "Weekly bulk CSV/JSON datasets: "
        + PRO_DATASET
        + " (free sample: "
        + FREE_SAMPLE
        + ")"
    )
