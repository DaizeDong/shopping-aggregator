"""Fail-closed eligibility check for a selected airfare's comparable total.

This validates declared evidence, not truth on a live booking page. Callers must
collect and independently verify the cited selected-source observations first.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, DecimalException, InvalidOperation
import json
from pathlib import Path
from urllib.parse import urlsplit

COSTS = ("fare", "tax", "checked_bags", "cabin_bags", "seat_selection", "payment_fx")
TERMS = COSTS + ("fare_brand", "refund_terms")


def assess_total(quote, now=None):
    now = now or datetime.now(timezone.utc)
    gaps, amounts = [], []
    if not isinstance(quote, dict):
        return {"status": "not_comparable", "gaps": ["quote"]}
    terms = quote.get("terms", {})
    if not isinstance(terms, dict):
        terms = {}
    for key in TERMS:
        term = terms.get(key)
        if not isinstance(term, dict) or term.get("status") != "verified":
            gaps.append(key)
            continue
        value = term.get("value")
        if key in COSTS:
            try:
                amount = Decimal(str(value))
                if isinstance(value, bool) or not amount.is_finite() or amount < 0:
                    raise InvalidOperation
                amounts.append(amount)
            except (DecimalException, ValueError):
                gaps.append(key)
        elif not isinstance(value, str) or not value.strip():
            gaps.append(key)
    if not isinstance(quote.get("currency"), str) or not re_currency(quote["currency"]):
        gaps.append("currency")
    variant = quote.get("variant_key")
    if not isinstance(variant, str) or not variant.strip():
        gaps.append("variant_key")
    transports = set()
    sources = quote.get("sources")
    if not isinstance(sources, list):
        sources = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        try:
            fetched = datetime.fromisoformat(source.get("fetched_at", ""))
            age = (now - fetched).total_seconds()
            url = urlsplit(source.get("source_url", ""))
        except (TypeError, ValueError):
            continue
        transport = source.get("transport_id")
        if (source.get("selected") is True and source.get("evidence_grade") == "E1"
                and source.get("variant_key") == variant and 0 <= age <= 4 * 3600
                and url.scheme == "https" and url.hostname and not url.username
                and isinstance(transport, str) and transport.strip()):
            transports.add(transport)
    if len(transports) < 2:
        gaps.append("two_independent_selected_E1_transports")
    if gaps:
        return {"status": "not_comparable", "gaps": gaps}
    try:
        total = sum(amounts).quantize(Decimal("0.01"))
    except DecimalException:
        return {"status": "not_comparable", "gaps": ["amount_total_out_of_range"]}
    if not total.is_finite():
        return {"status": "not_comparable", "gaps": ["amount_total_out_of_range"]}
    return {"status": "comparable_total", "currency": quote["currency"],
            "total": str(total),
            "claim_scope": "selected verified offers only"}


def re_currency(value):
    return len(value) == 3 and value.isascii() and value.isalpha() and value.isupper()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quote", type=Path, help="Private quote JSON; no output file is created")
    args = parser.parse_args()
    try:
        result = assess_total(json.loads(args.quote.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        result = {"status": "not_comparable", "gaps": ["unreadable_quote"]}
    print(json.dumps(result))
    return 0 if result["status"] == "comparable_total" else 1


if __name__ == "__main__":
    raise SystemExit(main())
