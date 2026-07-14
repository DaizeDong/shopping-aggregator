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
    print("make_fixtures: wrote %d scenario(s) -> %s" % (len(CASES), dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
