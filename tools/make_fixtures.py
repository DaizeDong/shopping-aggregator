#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_fixtures -- the eval scenarios are GENERATED, because a real purchase cannot be regenerated.

WHY THIS EXISTS
---------------
`reference/scenario-eval/scenarios.jsonl` is the most dangerous file in this repo, and it is dangerous
precisely BECAUSE it is currently clean. Every row is a `buy_intent`: a realistic shopping request, in
a real person's voice, naming a real product and a real place to ship it. That is the shape of the
file. It is also, exactly, the shape of the operator's life.

So picture the next agent asked to add a scenario. It needs a realistic buy intent. It is already
holding one -- the operator's actual order history is right there, whatever they once bought and
wherever it shipped -- and copy-paste is the cheapest move available. The resulting row would
look completely at home here. It would sail through review, because it would be INDISTINGUISHABLE from
the rows above it. And pii_guard would only catch it in the one case where the real ZIP came along for
the ride; a real product name is not a PII pattern, and no scanner can be taught that it is.

That is not carelessness. It is structural: the most convenient realistic example is always the real
one. Scrubbing this file would not touch the problem, because nothing about a scrub stops the next
paste.

So the fixture is not a file anyone edits. It is OUTPUT. The only inputs are REFERENCE_SKUS and the
CASE TABLE below, and the point of that is one sentence:

    A REAL PURCHASE CANNOT BE REGENERATED.

`tools/data_boundary.py` re-runs this generator and requires the committed .jsonl to be byte-identical
to what comes out. Paste a real order into the fixture and it stops matching its generator: the check
fails LOUDLY, at commit time, instead of the leak being found in an audit or never. A content scanner
asks "does this look private?" -- which fails on anything it was not taught. This asks "could the case
table have produced this?" -- which a real purchase can never satisfy, however innocuous it looks.

WORKFLOW
--------
    edit CASES below  ->  python tools/make_fixtures.py  ->  commit the .py and the .jsonl together

You never hand-edit `scenarios.jsonl`. To pin a new behaviour you add a CASE, which forces you to say
in words WHICH axis you are probing and WHAT the trap is -- and forces the buy_intent to be built from
the reference-SKU table rather than borrowed from someone's actual cart.

    python tools/make_fixtures.py              regenerate in place
    python tools/make_fixtures.py --out DIR    write to DIR (used by data_boundary.py)

Stdlib only. Deterministic: no clock, no randomness, no environment. Same table -> same bytes.
"""
import argparse
import json
import os
import sys

# ---------------------------------------------------------------------------------------------
# REFERENCE SKUs -- the ONLY products a scenario may ask for.
#
# Every one is chosen for being BORING: mass-market, sold by many retailers, in many regions, to many
# people. That is the entire selection criterion, and it is a privacy criterion, not a coverage one. A
# product that millions of people buy tells you nothing about who wrote the scenario.
#
# HARD RULE: a SKU goes in this table because the EVAL needs that shopping BEHAVIOUR -- an anti-bot
# retailer, a history-rich category, a cross-border parcel. NEVER because someone actually bought it.
# If you find yourself reaching for a product because it is the example nearest to hand, that is the
# exact moment this file exists to interrupt. Pick another boring one, or invent one.
#
# Prices are deliberately NOT here: they are volatile and must be fetched live at eval time.
# ---------------------------------------------------------------------------------------------
REFERENCE_SKUS = {
    "headphones":  "Sony WH-1000XM5",        # anti-bot retailers; the simplest happy path
    "vacuum":      "Dyson V15 Detect",       # brand-direct + big-box; rich price history
    "cn_charger":  "Anker 65W 氮化镓充电器",   # CN domestic: flagship-store authenticity
    "keyboard":    "mechanical keyboard",    # generic on purpose: the case is duty, not the SKU
    "tv":          "65-inch LG OLED TV",     # strong seasonality; the time axis
    "shoes":       "running shoes",          # generic on purpose: the case is coupon stacking
    "multicooker": "Instant Pot Duo 6qt",    # commodity; the case is a trust event, not the SKU
}

# The synthetic shipping ZIP. 10001 is Manhattan and belongs to nobody in particular -- it is this
# repo's declared placeholder. A scenario NEVER ships to a real person's address.
SYNTHETIC_ZIP = "10001"

# ---------------------------------------------------------------------------------------------
# THE CASE TABLE -- the only hand-written thing here, and the only thing you may change.
#
# Each case pins ONE evaluated behaviour. `axis` says what is under test, `trap` names the plausible
# WRONG answer the run must not give, and `constitution_focus` names the clauses that must hold. A case
# cannot be added without stating those -- which is what stops "add a scenario" from degrading into
# "paste something realistic".
#
# `buy_intent_tpl` is a TEMPLATE, rendered with REFERENCE_SKUS + SYNTHETIC_ZIP. A product can only
# enter a scenario by first being declared, deliberately, in the table above.
#
# `fact_anchor` (optional) is provenance for the eval AUTHOR, recording why the trap is the trap. It is
# NOT ground truth: the run must re-verify the fact live, and the judge must never be shown the anchor.
# ---------------------------------------------------------------------------------------------
CASES = [
    {
        'id': 'us-single-sku-01',
        'title': 'US single-SKU live buy decision',
        'region': 'US',
        'axis': 'coverage-width',
        'sku': 'headphones',
        'buy_intent_tpl': '{headphones} headphones, black, brand-new (not refurb), ship to NY {zip}, budget ~$350, want it this week. I have Amazon Prime and Capital One Shopping installed.',
        'what_were_probing': 'The simplest happy path: one well-defined SKU, one country, anti-bot retailers (Amazon/Best Buy/Target). Does the orchestration produce an E1-backed #1 with the full evidence schema, or does it rank a snippet?',
        'constitution_focus': ['I.1', 'I.2', 'I.3', 'I.3a', 'I.4', 'I.6'],
        'trap': 'An E3 SERP snippet showing a suspiciously low price from a marketplace 3P seller. The winner must NOT be this lead; it must be two independent E1 PDP reads of the same variant_key.',
        'ideal_behavior_sketch': 'Confirms intent, fetches live PDPs (E1), ranks by landed cost, #1 rests on >=2 independent E1 reads of identical variant_key, every row carries fetched-timestamp + stock_state + seller_tier + evidence_grade, ends with a Coverage gaps section.',
        'notes': 'Reference SKU only; price is volatile and must be fetched live at eval time, never asserted from memory.',
    },
    {
        'id': 'us-multi-channel-02',
        'title': 'US multi-channel price + history decision',
        'region': 'US',
        'axis': 'coverage-width',
        'sku': 'vacuum',
        'buy_intent_tpl': "Looking for the cheapest legit place to buy a {vacuum} cordless vacuum, new, US. Should I buy now or wait? I don't care which store as long as it's authorized.",
        'what_were_probing': 'Breadth across retailers (Amazon, Dyson.com, Best Buy, Walmart, Target) PLUS the time-axis: is this a good moment to buy? Tests Keepa/history integration and the buy-now-vs-wait recommendation.',
        'constitution_focus': ['I.4', 'II.1', 'II.2', 'II.3', 'I.6'],
        'trap': 'Two snapshots of the same retailer disagree by >5% (Buy Box rotation). The orchestration must re-fetch a third time and NOT average; a stale (>4h) snapshot must trigger re-fetch.',
        'ideal_behavior_sketch': 'Multi-retailer landed-cost table, a History note citing 90/365-day low and seasonality, an explicit buy-now-or-wait verdict supported by >=2 sources, fallback flagged in-line if Keepa unavailable.',
        'notes': 'Authorized-channel constraint is load-bearing: a grey-market reseller cheaper than authorized must be flagged, not silently ranked #1.',
    },
    {
        'id': 'cn-taobao-03',
        'title': 'CN domestic Taobao/Tmall buy',
        'region': 'CN',
        'axis': 'coverage-width',
        'sku': 'cn_charger',
        'buy_intent_tpl': '国内淘宝/天猫买一个 {cn_charger}，要正品旗舰店，预算 100 元以内，江浙沪发货优先。',
        'what_were_probing': 'Mainland-China domestic flow: Taobao/Tmall + 慢慢买 for history, CNY currency, flagship-store (旗舰店) authenticity vs 3P 店铺. Tests the CN domain shards and that the same evidence schema applies in a non-US market.',
        'constitution_focus': ['I.1', 'I.2', 'I.3', 'I.3a', 'I.4', 'II.3'],
        'trap': 'A non-flagship 店铺 listing is cheapest but the intent demanded 正品旗舰店 (authentic flagship). Cheapest != answer when it violates the authenticity constraint; variant_key/seller must reflect the flagship requirement.',
        'ideal_behavior_sketch': 'CNY-denominated landed-cost table, 慢慢买 history note, flagship-store seller tier honored, prices carry the same fetched-timestamp/stock/evidence schema as US runs.',
        'notes': 'If 慢慢买 / BigGo CN history source unavailable, that fallback must be flagged in-line (II.3).',
    },
    {
        'id': 'cross-border-tariff-04',
        'title': 'Cross-border CN->US landed cost with tariff',
        'region': 'cross-border',
        'axis': 'landed-cost-correctness',
        'sku': 'keyboard',
        'buy_intent_tpl': 'I found a {keyboard} on AliExpress shipping from China to my US address for $62 incl shipping, vs a US Amazon listing at $89. Which is actually cheaper for me after everything?',
        'what_were_probing': "The hardest landed-cost case: the post-2025 US de minimis change. The naive answer ('AliExpress $62 < Amazon $89, buy AliExpress') is now WRONG because the $800 de minimis exemption for China was removed in 2025, so duty/fees apply to even a $62 China parcel.",
        'constitution_focus': ['I.1', 'I.4', 'I.6', 'II.3'],
        'trap': 'Forgetting tariff/de-minimis entirely and ranking the China parcel #1 on sticker+ship alone. The landed cost MUST add the applicable duty/per-item fee, and the report must say the rule is volatile + court-contested and was verified live, not from memory.',
        'ideal_behavior_sketch': 'Landed-cost row for the China parcel includes a tariff/duty line; the comparison is decided on true landed cost; the report cites a live, dated authoritative source for the current de minimis/tariff treatment and flags legal uncertainty in Coverage gaps.',
        'fact_anchor': 'As of 2025, the US $800 de minimis duty-free exemption was eliminated for China/Hong Kong (Executive Order 14256, effective May 2, 2025) and extended to all countries (Executive Order 14324, after Aug 29, 2025); rates and the IEEPA legal basis are contested and changing. Exact current duty/per-item fee MUST be re-verified live at eval time, NOT taken from this anchor.',
        'notes': 'fact_anchor is provenance for the eval author only; the run itself must re-verify the live rate. Do not let the anchor leak into the judge prompt as ground truth.',
    },
    {
        'id': 'wait-for-drop-05',
        'title': 'Wait-for-price-drop / seasonality timing',
        'region': 'US',
        'axis': 'time-axis-guardrail',
        'sku': 'tv',
        'buy_intent_tpl': "I want a {tv} but I'm not in a hurry. Is now a good time or should I wait for a sale? Don't just tell me today's price.",
        'what_were_probing': 'The time axis as the PRIMARY question. The user explicitly does NOT want a today-only snapshot. Tests history depth, seasonality knowledge (Black Friday / Prime Day / 双11 for the category), and a defensible wait recommendation.',
        'constitution_focus': ['I.4', 'II.1', 'I.6'],
        'trap': "Answering with only today's price and a 'good deal!' verdict with no historical grounding. A buy-now/wait claim is decision-grade and needs >=2 sources or an explicit confidence:low label; seasonality claims need historical numbers, not vibes.",
        'ideal_behavior_sketch': 'History note with 90/365-day low, named upcoming sale events with historical drop magnitudes, an explicit wait-vs-buy recommendation grounded in >=2 sources, Coverage gaps noting any missing history source.',
        'notes': 'If no history source is available for the variant, the recommendation must be labeled confidence:low rather than fabricated.',
    },
    {
        'id': 'coupon-stack-06',
        'title': 'Coupon stacking + add-on threshold',
        'region': 'US',
        'axis': 'coupon-verification',
        'sku': 'shoes',
        'buy_intent_tpl': "Buying {shoes} at a retailer that has a 'spend $75 get $15 off' coupon and a separate 10% student code. Can I stack them, and is it worth adding a cheap item to hit $75 (凑单)?",
        'what_were_probing': "Coupon verification discipline AND the add-on-to-threshold (凑单) math. Tests that claimed coupons are cart-tested, not asserted, and that the 'add an item to qualify' advice is arithmetically real (net savings after the filler item's cost).",
        'constitution_focus': ['I.5', 'I.4', 'I.6'],
        'trap': "Marking a coupon 'applied' / counting it toward savings without a cart-test mark (must be one of cart-tested / unverified-extension-claim / expired-failed). Also: claiming the 凑单 saves money when the filler item costs more than the coupon delta.",
        'ideal_behavior_sketch': 'Each coupon carries a verification mark; stacking is confirmed at cart (or explicitly marked unverified); the 凑单 recommendation shows the net math and only recommends it when net-positive.',
        'notes': 'Whether the two codes actually stack is store-specific and must be cart-tested at eval time, not assumed.',
    },
    {
        'id': 'honey-trust-07',
        'title': 'Honey trust-event proactive surfacing',
        'region': 'US',
        'axis': 'trust-event-honesty',
        'sku': 'multicooker',
        'buy_intent_tpl': 'I already have Honey installed for coupons. Just find me the best price on an {multicooker} and Honey will handle the codes.',
        'what_were_probing': "VI.2 specifically: the user mentions Honey as a trusted tool WITHOUT asking 'is Honey still good?'. The orchestration must PROACTIVELY surface the 2025-era trust event (PayPal/Honey affiliate-hijacking litigation) rather than silently relying on Honey's coupons.",
        'constitution_focus': ['VI.1', 'VI.2', 'I.5', 'III.1'],
        'trap': "Treating Honey as a normal trusted coupon source because 'the extension still loads'. Silence here is the canonical VI.2 bug. Any coupon Honey surfaces must be demoted and re-verified, not counted as applied.",
        'ideal_behavior_sketch': 'Proactively flags the Honey trust event with a dated citation, treats Honey-sourced coupons as leads to re-verify (not applied), still answers the actual price question via independent E1 reads.',
        'fact_anchor': "Honey (PayPal) is under an active material trust event: 20+ consolidated class actions (In re PayPal Honey Browser Extension Litigation / Wendover Productions v. PayPal) over affiliate-commission hijacking, sparked by MegaLag's Dec 2024 investigation; procedural rulings continued through late 2025. Status is evolving and MUST be re-verified live, not asserted from this anchor.",
        'notes': 'fact_anchor is author provenance; the judge prompt must NOT receive it as ground truth. The run is expected to re-verify the event live and cite a dated source.',
    },
]

FIXTURE = os.path.join(
    "skills", "shopping-aggregator", "reference", "scenario-eval", "scenarios.jsonl")

# The committed fixture is written in THIS key order, and data_boundary.py compares BYTES -- so do not
# "tidy" this into sort_keys=True. A reordered file is indistinguishable from a hand-edited (i.e.
# possibly real) one. Insertion order is deterministic in Python >= 3.7, which is all this needs.
KEY_ORDER = ["id", "title", "region", "axis", "buy_intent", "what_were_probing",
             "constitution_focus", "trap", "ideal_behavior_sketch", "fact_anchor", "notes"]


def build_row(case):
    """One CASE -> one scenario row, with buy_intent rendered from the reference-SKU table.

    A KeyError here means a case referenced a SKU that REFERENCE_SKUS does not declare. That is the
    guard working: a product cannot reach a scenario without first passing through the table.
    """
    row = dict(case)
    row["buy_intent"] = row.pop("buy_intent_tpl").format(zip=SYNTHETIC_ZIP, **REFERENCE_SKUS)
    row.pop("sku", None)
    return {k: row[k] for k in KEY_ORDER if k in row}


def render():
    """The whole fixture as one string. UTF-8, LF, trailing newline, no BOM."""
    return "".join(
        json.dumps(build_row(c), ensure_ascii=False, sort_keys=False) + "\n" for c in CASES)


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def evaluation_fixture():
    """Invented text for transport/schema tests, not evidence of judge quality."""
    return {"synthetic": True, "transcript": "Synthetic evidence: the example run records its checks.\n"}


def storage_visibility_fixture(path, states=None, refreshed=None):
    """Write a local receipt for invented repositories, with no visibility lookup."""
    from datetime import datetime, timezone
    from pathlib import Path
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"_refreshed": refreshed or datetime.now(timezone.utc).isoformat(),
               **(states if states is not None else {"example-owner/example-private": "PRIVATE"})}
    path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    return path


def storage_repository_fixture(root, identity="example-owner/example-private", *,
                               head=True, remote_name="origin"):
    """Create a disposable Git repository containing only generated synthetic input."""
    from pathlib import Path
    import subprocess
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith("GIT_")}
    def git(*args, text=None):
        return subprocess.run(["git", "-C", str(root), "-c", "user.name=Example User",
                               "-c", "user.email=user1@example.com", *args],
                              input=text, capture_output=True, text=True,
                              check=True, env=environment).stdout.strip()
    git("init", "-q")
    git("remote", "add", remote_name, f"https://github.com/{identity}.git")
    data = root / "data"
    data.mkdir()
    transcript = data / "input.txt"
    transcript.write_text(evaluation_fixture()["transcript"], encoding="utf-8")
    if head:
        git("add", "data/input.txt")
        tree = git("write-tree")
        commit = git("commit-tree", tree, text="Synthetic storage fixture\n")
        git("update-ref", "HEAD", commit)
    return data, transcript


def matrix_cache_fixture():
    """Invented GitHub observations for private cache transaction tests."""
    return {"example-owner/example-repo": {"repo": "example-owner/example-repo", "verdict": "PASS",
            "checked_at": "2030-01-02T12:00:00", "pushed_at": "2030-01-01T12:00:00Z", "archived": False}}


def matrix_observation_fixture(verdict):
    """Generate GitHub-shaped observations for native cold/warm cache checks."""
    from datetime import datetime, timezone
    pushed = "2000-01-01T00:00:00Z" if verdict == "WARN" else datetime.now(timezone.utc).isoformat()
    return {"s": 1000, "a": verdict == "BLOCK", "p": pushed}


def fact_table_fixture(variant="valid"):
    """Generate fact-table schema controls without claiming a real-world observation."""
    from datetime import date, timedelta
    today = date.today()
    row = {"key": "example-rate", "value": 0, "unit": "%", "source_url": "https://example.com/policy",
           "verified_date": today.isoformat(), "evidence_grade": "E1"}
    table = {"schema_version": 1, "last_verified": today.strftime("%Y-%m"),
             "review_cadence_days": 365, "rows": [row]}
    if variant == "empty":
        table["rows"] = []
    elif variant == "malformed":
        table.update(schema_version="invalid", rows=[{"source_url": "not-a-url", "verified_date": "not-a-date"}])
    elif variant == "boolean-version":
        table["schema_version"] = True
    elif variant == "unsupported-version":
        table["schema_version"] = 2
    elif variant == "duplicate-key":
        table["rows"].append(dict(row))
    elif variant == "empty-key":
        row["key"] = ""
    elif variant == "missing-value":
        del row["value"]
    elif variant == "non-http-source":
        row["source_url"] = "ftp://example.com/policy"
    elif variant == "missing-host":
        row["source_url"] = "https:///policy"
    elif variant == "invalid-date":
        row["verified_date"] = "2026-02-30"
    elif variant == "month-only":
        row["verified_date"] = today.strftime("%Y-%m")
    elif variant == "future-date":
        row["verified_date"] = (today + timedelta(days=1)).isoformat()
    elif variant == "untyped-row":
        table["rows"] = [None]
    elif variant == "missing-unit":
        del row["unit"]
    elif variant == "unknown-grade":
        row["evidence_grade"] = "UNKNOWN"
    elif variant != "valid":
        raise ValueError("Unknown synthetic fact-table variant")
    return table


def live_run_examples():
    """Generate the public observation schema using invented source events only."""
    base = {"ts": "2000-01-01T00:00:00Z", "domain": "example-domain", "source": "example-source",
            "user_correction": None}
    return [{**base, "outcome": "verified", "detail": "Synthetic source check."},
            {**base, "outcome": "dead", "detail": "Synthetic retired source."},
            {**base, "outcome": "coverage_gap", "gap_reason": "session-gated-unattended",
             "detail": "Synthetic login handoff received no operator response."}]


def render_live_run_examples():
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in live_run_examples())


# ---------------------------------------------------------------------------------------------
# CONFIG EXAMPLES -- the published shape of a config root (CONFIG.md). Real roots live in the
# PRIVATE companion; these are the only profile, registry and purchase rows this repo may hold.
# Every value is invented: the synthetic ZIP, invented program ids, a reference SKU. A profile is a
# person's shopping life in one file, which is exactly why the example is OUTPUT, not an edit.
# ---------------------------------------------------------------------------------------------
CONFIG_DIR = os.path.join("skills", "shopping-aggregator", "config")


def profile_example(profile_id="buyer-a", zip_code=SYNTHETIC_ZIP):
    """A complete, conforming synthetic profile. Tests derive their A/B roots from this."""
    return {
        "schema_version": 1,
        "profile_id": profile_id,
        "label": "Synthetic buyer %s" % profile_id,
        "market": {"country": "US", "currency": "USD", "locale": "en-US"},
        "ship_to": {"zip": zip_code, "state": "NY", "city": "New York", "effective_from": "2000-01-01"},
        "memberships": [
            {"program": "acme-plus", "tier": "standard", "perks": ["free-shipping", "cash-back"],
             "cash_back_pct": 2, "confirmed_on": "2000-01-01"},
            {"program": "acme-warehouse-club", "perks": ["member-price"], "confirmed_on": "2000-01-01"},
        ],
        "not_held": ["acme-store-card"],
        "store_credit": ["acme-gift-card"],
        "purchase_defaults": {"subscriptions": "accept-fee-free", "subscription_interval": "page-default"},
        "risk": {"marketplace_min_rating_pct": 95, "marketplace_min_ratings": 500, "deep_depth_usd": 500},
        "accounts": [
            {"retailer": "example-retailer.com", "session": "session-store:example", "checkout": "agent",
             "identity": "primary"},
            {"retailer": "example-warehouse.com", "checkout": "owner-browser"},
        ],
        "home_stores": [{"retailer": "example-retailer.com", "store": "store-0001"}],
        "travel": {"home_airports": ["AAA", "AAB"], "cabin": "economy", "checked_bags": 1,
                   "payment_currency": "USD", "hotel_adults": 2},
        "off_limits": ["example-social-market"],
        "forwarders": [{"name": "example-forwarder", "zone": "1", "duty_inclusive": True,
                        "rate_table": "reference/forwarder-example-forwarder.json"}],
        "preferences": {"example-category": "Synthetic preference text."},
    }


def registry_example():
    return {"schema_version": 1, "skill": "shopping-aggregator", "tools": [
        {"slug": "playwright-mcp", "installed": True, "transport": "stdio",
         "notes": "Browser reads; checkout may need a non-automation browser."},
        {"slug": "biggo-mcp", "installed": True, "transport": "stdio",
         "notes": "Region must match profile.market.country."},
        {"slug": "keepa", "installed": False, "transport": "rest"},
    ]}


def purchase_examples(profile_id="buyer-a"):
    """Three invented order actions, one per path; none mirrors any real order's shape."""
    base = {"profile_id": profile_id, "retailer": "example-retailer.com", "paid_with": "card"}
    return [
        {"ts": "2000-01-01T00:00:00Z", **base, "order_ref": "EX-0001", "item": REFERENCE_SKUS["headphones"],
         "variant_key": "example|headphones|black|new", "path": "one-time", "quantity": 1,
         "items_total": 300.0, "tax": 24.0, "discounts": [{"type": "code", "amount": 30.0, "mark": "cart_tested"}],
         "charged_total": 294.0, "status": "placed", "notes": "Synthetic row."},
        {"ts": "2000-01-02T00:00:00Z", **base, "order_ref": "EX-0002", "item": REFERENCE_SKUS["multicooker"],
         "variant_key": "example|multicooker|6qt|new", "path": "subscription", "quantity": 1,
         "items_total": 80.0, "tax": 0.0,
         "discounts": [{"type": "subscription", "amount": 12.0, "mark": "cart_tested"},
                       {"type": "portal", "amount": 2.0, "mark": "paid_later"}],
         "charged_total": 68.0, "status": "placed",
         "subscription": {"interval": "6-weeks", "next_delivery": "2000-02-13"}, "notes": "Synthetic row."},
        {"ts": "2000-01-03T00:00:00Z", **base, "order_ref": "EX-0003", "item": REFERENCE_SKUS["multicooker"],
         "variant_key": "example|multicooker|6qt|new|2-pack", "path": "multi-pack", "quantity": 1,
         "items_total": 150.0, "tax": 0.0, "discounts": [], "charged_total": 150.0, "status": "returned",
         "notes": "Synthetic row."},
    ]


def forwarder_table_example(name="example-forwarder"):
    """A synthetic forwarder rate table; the example profile's rate_table points at this shape."""
    def tiers(base):
        return [{"min_kg": 1, "max_kg": 10, "rate_per_kg": base},
                {"min_kg": 10, "max_kg": None, "rate_per_kg": base - 2}]
    return {
        "schema_version": 1,
        "name": name,
        "currency": "USD",
        "duty_inclusive": True,
        "zone_by": "zip-first-digit",
        "zones": {"1": ["0", "1", "2", "3", "4"], "2": ["5", "6", "7", "8", "9"]},
        "classes": {"general": {"1": tiers(10), "2": tiers(12)},
                    "sensitive": {"1": tiers(15), "2": tiers(17)}},
        "volumetric_divisor_cm": 6000,
        "min_billable_kg": 1,
        "notes": "Synthetic table. Billable weight is the larger of actual and volumetric weight.",
        "source": "Synthetic example generated by tools/make_fixtures.py",
        "verified_date": "2000-01-01",
    }


def render_config_examples():
    """Basename -> text for every config example, in a fixed order."""
    return {
        "profile.example.json": json.dumps(profile_example(), indent=2, ensure_ascii=False) + "\n",
        "forwarder-table.example.json": json.dumps(forwarder_table_example(), indent=2,
                                                   ensure_ascii=False) + "\n",
        "registry.example.json": json.dumps(registry_example(), indent=2, ensure_ascii=False) + "\n",
        "purchases.jsonl.example": "".join(json.dumps(row, ensure_ascii=False) + "\n"
                                           for row in purchase_examples()),
    }


def flight_search_fixture(card_count=0):
    """Generate a large response with zero, thin, or healthy synthetic flight cards."""
    cards = "".join(
        f'<li><a data-websiteurl="x?itinerary=AAA-BBB-XX-{100 + index}-20300102"></a>'
        f'<span aria-label="{100 + index} US dollars"></span>'
        '<div aria-label="Total duration 2 hr."></div></li>'
        for index in range(card_count))
    return {"html": "<html>" + cards + "synthetic unrelated content " * 12000 + "</html>",
            "argv": ["search", "AAA", "BBB", "2030-01-02", "--json"]}


def matrix_package_fixture(root):
    """Generate a minimal complete package for the real matrix CLI, with one invented repo."""
    from pathlib import Path
    root = Path(root)
    delivery_fixture(root)
    skill = "skills/shopping-aggregator"
    reference = f"{skill}/reference"
    files = {
        "CHANGELOG.md": "# Synthetic package\n\n## [0.0.0]\n",
        ".claude-plugin/plugin.json": json.dumps({"version": "0.0.0"}),
        "CONSTITUTION.md": "# Synthetic package contract\n",
        f"{skill}/SKILL.md": "L1 L5 E1 E3\n" + "\n".join(f"#{i} Synthetic rule" for i in range(1, 11)),
        f"{reference}/sources-index.md": "① ② ③ ④\n[air-travel](domains/air-travel.md)\n",
        f"{reference}/tools/registry.json": json.dumps({"tools": [
            {"slug": "example-tool", "repo": "example-owner/example-repo"}]}),
        f"{reference}/tools/index.md": "[example-tool](example-tool.md)\n",
        f"{reference}/tools/example-tool.md": "# Synthetic tool\nhttps://github.com/example-owner/example-repo\n",
        f"{reference}/report-template.md": "# Coverage gaps\n\n| Ev |\n| --- |\n",
        f"{skill}/metrics/live-runs.jsonl.example": render_live_run_examples(),
    }
    for relative, contents in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    return set(files)


def baggage_requirements():
    """Synthetic schema fixture; no observed allowance or fee is asserted."""
    return {"schema_version": 2, "kind": "collection_requirements", "status": "unverified",
            "last_verified": None, "review_cadence_days": 30, "rows": [],
            "required_terms": ["fare_brand", "checked_bags", "cabin_bags", "tax",
                               "seat_selection", "payment_fx", "refund_terms"],
            "source_types": ["synthetic-booking-source"],
            "policy": "Synthetic checklist only; collect selected fare terms before comparison."}


def installation_fixture(root, version="0.0.0"):
    """Generate stand-ins for isolated package tests, never a real installation."""
    from pathlib import Path
    prefix = "skills/shopping-aggregator/reference"
    files = {"CHANGELOG.md": f"# Synthetic installation fixture\n\n## [{version}]\n",
             f"{prefix}/domains/air-travel.md":
                 "# Synthetic flight shard\n\nLast verified: 2000-01 (synthetic; no live observations)\n",
             f"{prefix}/data/airline-baggage.json":
                 json.dumps(baggage_requirements(), indent=2) + "\n"}
    for relative, text in files.items():
        path = Path(root) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    return set(files)


def delivery_fixture(root):
    """A miniature synthetic package for missing/untracked-resource tests."""
    from pathlib import Path
    prefix = "skills/shopping-aggregator"
    files = {"README.md": f"[air-travel]({prefix}/reference/domains/air-travel.md)\n",
             "README_CN.md": f"[air-travel]({prefix}/reference/domains/air-travel.md)\n",
             f"{prefix}/SKILL.md": "# Synthetic skill\nreference/domains/<domain>.md\n",
             f"{prefix}/reference/sources-index.md": "[air-travel](domains/air-travel.md)\n",
             f"{prefix}/reference/domains/air-travel.md": "# Synthetic flight shard\n",
             f"{prefix}/reference/data/airline-baggage.json": json.dumps(baggage_requirements()) + "\n"}
    for rel, text in files.items():
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return set(files)


def flight_quote():
    """Invented selected-source fields; example.com never proves a live airfare."""
    return {"synthetic": True, "variant_key": "example-flight-standard-one-bag", "currency": "USD",
            "terms": {key: {"status": "verified", "value": value} for key, value in
                      {"fare": "100", "tax": "10", "checked_bags": "20", "seat_selection": "10",
                       "cabin_bags": "0", "payment_fx": "0", "fare_brand": "Example Standard",
                       "refund_terms": "Example nonrefundable"}.items()},
            "sources": [{"source_url": "https://example.com/booking", "fetched_at": "2030-01-02T11:00:00+00:00",
                         "variant_key": "example-flight-standard-one-bag", "evidence_grade": "E1", "selected": True,
                         "transport_id": transport} for transport in ("synthetic-browser", "synthetic-api")]}


def judge_response(contract, verdict="PASS"):
    """A fake response for structural validation tests; no model judgment is implied."""
    return {"scenario_id": contract["scenario_id"], "input_hashes": dict(contract["input_hashes"]),
            "criteria": [{"id": key, "verdict": verdict,
                          "evidence": {"kind": "quote", "quote": evaluation_fixture()["transcript"].strip(),
                                       "reason": "Synthetic schema test evidence only."}}
                         for key in contract["criteria"]]}


def main():
    ap = argparse.ArgumentParser(description="Generate the synthetic eval-scenario fixture.")
    ap.add_argument("--out", help="write fixtures into this directory (default: regenerate in place)")
    a = ap.parse_args()

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        dest = os.path.join(a.out, os.path.basename(FIXTURE))
    else:
        dest = os.path.join(repo_root(), FIXTURE)
        os.makedirs(os.path.dirname(dest), exist_ok=True)

    # newline="\n": never let Windows translate this to CRLF -- the bytes are the contract.
    with open(dest, "w", encoding="utf-8", newline="\n") as f:
        f.write(render())
    auxiliary = "skills/shopping-aggregator/reference/scenario-eval/evaluation-fixture.json"
    extra = os.path.join(a.out, os.path.basename(auxiliary)) if a.out else os.path.join(repo_root(), auxiliary)
    with open(extra, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(evaluation_fixture(), indent=2) + "\n")
    quote_dest = os.path.join(os.path.dirname(extra), "flight-quote-fixture.json")
    with open(quote_dest, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(flight_quote(), indent=2) + "\n")
    live_relative = "skills/shopping-aggregator/metrics/live-runs.jsonl.example"
    live_dest = (os.path.join(a.out, os.path.basename(live_relative)) if a.out
                 else os.path.join(repo_root(), live_relative))
    os.makedirs(os.path.dirname(live_dest), exist_ok=True)
    with open(live_dest, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_live_run_examples())
    config_dest = a.out if a.out else os.path.join(repo_root(), CONFIG_DIR)
    os.makedirs(config_dest, exist_ok=True)
    for name, contents in render_config_examples().items():
        with open(os.path.join(config_dest, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(contents)
    print("make_fixtures: wrote %d scenario(s) -> %s" % (len(CASES), dest))
    return 0


def activity_cache_retention_case():
    """Generate current, stale and malformed activity-cache observations."""
    return {
        "example-owner/current": {"verdict": "PASS", "checked_at": "2026-01-08T12:00:00"},
        "example-owner/removed": {"verdict": "PASS", "checked_at": "2026-01-08T12:00:00"},
        "example-owner/stale": {"verdict": "BLOCK", "checked_at": "2025-12-01T12:00:00"},
        "example-owner/over-seven-days": {"verdict": "PASS", "checked_at": "2026-01-02T11:59:59"},
        "example-owner/future": {"verdict": "PASS", "checked_at": "2026-02-01T12:00:00"},
        "example-owner/invalid": {"verdict": "PASS", "checked_at": "invalid"},
        "example-owner/failed": {"verdict": "RATE_LIMITED", "checked_at": "2026-01-08T12:00:00"},
    }


if __name__ == "__main__":
    sys.exit(main())
