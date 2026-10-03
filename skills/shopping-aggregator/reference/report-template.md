# Report template (shopping-aggregator)

> Snapshot: <YYYY-MM-DD HH:MM TZ> · Depth: <quick|standard|deep> · Region: <US|CN|cross-border>
> Currency: <USD|CNY|...> · Sources used this run: <playwright | BigGo | Keepa | 慢慢买 | ...>
> Fallbacks used: <e.g. "BigGo MCP not connected → playwright per-retailer"> · Coverage gaps: <list>

## Buy intent (confirmed with user)

- **Product**: <brand + model + spec + condition>
- **Region / market**: <US (NJ) | CN mainland | cross-border>
- **Budget / urgency**: <"<$X" | "willing to wait for sale" | "need by Wed">
- **Sensitivity**: <warranty / refurb-OK / seller-rating cutoff / shipping speed>
- **Existing accounts / extensions**: <e.g. Amazon Prime + Capital One Shopping>

> If the report misunderstood the intent above, stop reading, tell me and I'll re-run.

## Landed-cost ranking (the answer)

> One row per `variant_key` and purchase path. **Ev** = evidence grade: E1 live PDP/API · E2 aggregator · E3 snippet
> (a lead, never the ranked winner). Only an E1 row may be #1 (guardrail #5b).
> Each purchase path of an offer (one-time, subscription, ...) is its own row, ranked on the amount charged at
> checkout after its tested discount stack (guardrail #16): Landed = Sticker + Ship + Tax - Discounts, where
> Discounts holds only cart-tested lines. Value paid later (cash back, portal) goes in its own column and is
> never subtracted. The headline answer is the #1 row, never a sticker the run did not try to beat.

| Rank | Retailer | Variant (key) | Path | Sticker | Ship | Tax | Discounts (#16) | **Landed** | Paid later | Seller / tier | **Ev** | Stock / delivery | Snapshot |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | <retailer.com> | <brand model color edition / new> | <subscription, every N months> | $X | $Y | $Z | -$D | **$L** | +$K <form> | <name>, L1 | E1 | in_stock / <promise> | <ts> |
| 2 | <same retailer> | <same key> | one-time | $X | $Y | $Z | -$0 | **$L2** | | <name>, L1 | E1 | in_stock / <promise> | <ts> |
| ... | | | | | | | | | | | | | |

**But actually** (footnote on top picks):
- Top pick has <warranty / return policy / shipping speed> better than #2; if user values that, it's
  worth the $X premium.
- #2 ships from <region> in <time>, confirm shipping speed before defaulting to "cheapest."
- (Etc.)

## Discount stack behind the headline (guardrail #16)

| Discount | Amount | Condition (commitment, minimum, expiry, eligibility) | Mark (CONSTITUTION I.5) |
|---|---|---|---|
| <subscription / auto-replenish> | -$S | <cancel anytime, no fee, no minimum deliveries; interval; next charge date> | ✓ cart-tested |
| <coupon, incl. first-order coupon> | -$C | <clip required; renders only after selecting the path> | ✓ cart-tested |
| <code from cart or deal site> | -$P | <one per order; expiry> | ⚠ unverified / ✗ expired-failed |
| <cash back / portal / rewards earned> | +$K later | <form: cash or store credit; expiry; one portal per order> | paid later, not subtracted |

Where the run looked: <each purchase path selected, coupon page, cart, code sites>. Discounts that need a sign-up
(membership, trial, email list, store card) are listed as the buyer's option with their cost, never applied by the agent.

## History note (decision-grade)

- **Current price vs 90-day low**: <"at 90-day low" | "$X above 90-day low" | "NEW LOW">
- **Current price vs 365-day low**: <...>
- **Seasonality**: <"this category drops on Black Friday / Prime Day / 双 11" + historical numbers>
- **Recommendation**: <"buy now" | "wait, likely to drop ~$X by <event>" | "buy if you need it; not a deal but not bad">
- **History source**: <Keepa | Camelcamelcamel | 慢慢买 | none-available>; link to chart.

## Coupon-applied list (verified)

| Code | Applied | Savings | Source | Notes |
|---|---|---|---|---|
| <CODE1> | ✓ cart-tested | $X | <where it came from> | <e.g. "stacks with Prime"> |
| <CODE2> | ⚠ unverified | claimed $Y | <extension showed it but not tested> | confirm at checkout |
| <CODE3> | ✗ expired / failed | n/a | n/a | dropped from analysis |

If Honey was the source of any claimed coupon, demote and re-verify, see
`domains/browser-extensions.md` for the 2026 status.

## Risks & counter-evidence (mandatory)

- **Counterfeit / fake-seller risk**: <reverse-search findings, "ABC Electronics on eBay has 30+
  reviews calling out non-OEM units, recommend skipping" or "actively reverse-searched, none found
, not proof of safety">.
- **Refurb caveat**: <only if refurb in ranking, battery cycle disclosure, warranty length, who's
  doing the refurb (manufacturer vs 3P)>.
- **Cross-border / shipping risk**: <duties, "may take 4-6 weeks if shipped from CN", "no
  manufacturer warranty on grey-market">.
- **Buy Box volatility**: <if multiple snapshots disagreed, state the band: "price band $X-$Y over
  last 4 hours, Buy Box rotating">.
- **Coupon-extension trust**: <re Honey alleged hijack, if any savings came from an extension,
  state who got the affiliate credit>.

If nothing found, state explicitly: "actively reverse-searched, none found, not proof of safety."

## Disagreement matrix (when sources diverged)

> Only compare **same-`variant_key`** prices here, different variants are separate SKUs, not
> disagreements. Cause ∈ {different seller, stale/aggregated (E2/E3), coverage-gap}. Resolve by
> evidence grade (E1 wins), never average.

| Claim | Source A | Source B | Cause | Lean |
|---|---|---|---|---|
| 90-day low | Keepa: $89 | Camelcamelcamel: $79 | Keepa misses some 3P deals; Camel includes Warehouse | Camel ($79) |
| Live Buy Box | playwright 14:32: $129 | playwright 14:38: $134 | rotated to 3P seller | re-fetch 3x; band $129-134 |

## Sources

Full list with tier + timestamp. Mark `✓verified / ⚠unverifiable / ✗dead`.

- [<retailer.com>](<url>), L1 first-party · **E1 PDP-read** · fetched 2026-MM-DD HH:MM · ✓verified
- [Camelcamelcamel](https://camelcamelcamel.com/product/<asin>), L2 history · ✓verified
- ...

## Optional sections (use when relevant)

Place any optional sections before the final **Coverage gaps** section.

### Coupon stacking strategy

If user is comfortable with multi-step checkout, describe:
1. Open retailer page in **incognito** (so no prior extension session interferes).
2. Apply public code <X>.
3. Stack <Y> from Slickdeals thread.
4. Final landed cost: $<lower>.

### "Wait for sale" projection

If urgency = "can wait":
- Historical: this category drops <X%> around <event> (Prime Day / Black Friday / 618 / 双 11).
- Camelcamelcamel chart shows similar SKUs hit floor in <month>.
- Recommend: wait until <date>; if price doesn't drop by then, buy at current.

### Trade-in / sell-old-one credit

If applicable (phones, laptops, electronics):
- Apple Trade-In / Samsung Trade-In / Amazon Trade-In quote estimates.
- 3P alternatives: Gazelle, Decluttr, ItsWorthMore.
- True net cost after trade-in.

## Coverage gaps

This section is mandatory and MUST be last, after Sources and any optional sections (CONSTITUTION I.6).
If no gaps remain, state explicitly: "actively reverse-searched, none found".

Every row carries a **typed reason** (CONSTITUTION II.8), because "one login away" and "no login
helps" are different facts and the next run should treat them differently.

| channel / dimension | gap reason | what it would have bought | retry next run? |
|---|---|---|---|
| <C2C secondhand> | `session-gated-declined` | <the going secondhand rate, the only channel carrying it> | **yes**, one operator login |
| <marketplace X> | `session-gated-unattended` | <live listings> | **yes**, if run attended |
| <region-locked store> | `structurally-unreachable` | <nothing a login fixes> | no |
| <aggregator Y> | `tool-outage` | <cross-store sweep> | yes, when the MCP is back |
| <class Z> | `not-attempted` | <in-scope class never queried, say why> | yes |

- **Zeros are qualified**: any "no listings found" from a marketplace states its **control query** and
  that query's result (guardrail #11). Without one, the zero is not reportable.
- **No backfilling**: a gapped cell is left empty. Another channel's numbers do not answer a question
  about this one; say the cell is empty and move on.
- **Configure for deeper data**:
  - "<retailer/dimension> would be stronger with <source>, install via <command> (then reconnect)."
  - e.g. "Amazon history would be stronger with Keepa MCP, install via `~/.claude.json` edit (€49/mo)."
