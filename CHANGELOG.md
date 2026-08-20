# Changelog

## [0.7.1], 2026-08-20

**Distilling a run into the tool, and one entry that says a dead MCP is not a dead capability.** A cross-border consumer run produced failures that were all about *reading* rather than pricing, so they graduate into `reference/source-reliability.md` per the Step 7 rule: source and retailer-class properties only, with the shopping list stripped.

- **The browser section gains the recovery that mattered most.** A browser MCP reported `Connected` in the health listing while its tools resolved from the deferred registry not at all, by keyword and by exact name, in the main session and in twelve subagents alike. When the health line and the tool registry disagree, the health line is the one lying (#6, again). The entry now says to check for a locally installed browser library before writing a browser-only channel off: driving it from the shell against the operator's already-persisted session restored a channel no other route could reach, after the outage had already been written up as unreachable.
- **Reading a search result page gains three signatures.** A sort parameter can be **inert**, returning an id sequence identical position-for-position to no sort while a different sort surfaces ids the first pass never saw, which makes it a broken measuring instrument in exactly the way an ignored page param is. Some sites **render their own zero** (a nothing-found string, a 1-of-1 counter, a grid backfilled with unrelated stock), which is distinguishable from a block on sight. And a price can be **split across sibling DOM nodes with the live price first**, so a largest-number regex reads the struck-through original and an unbounded one welds the price to the following counter.
- **Listing-page truth gains four.** A brand-direct **restock alert may not exist at all** (one first-party store had zero notify strings in its entire UI table, and its "Back in Stock" link was a browse category), so do not promise one without checking. **One listing can BE the market**, which turns a buyer's anchor price into a ceiling rather than a rate. **A regional reissue is not automatically the same article**, and the existence of a domestic-versus-imported comparison video is itself evidence the two differ. And **the decoy field around a sought-after item can hold five or more distinct objects**, where price band does not discriminate them because the bands overlap; only stated dimensions, weight and a manufacturer id do.
- **Cross-border gains the naming rule.** On a non-English platform, query the **local** name before concluding the platform has none. The English-name query returned a self-rendered zero on a platform that carried pages of matches under the local name, including an entire regional official release absent from every English and Japanese source. Getting the local name wrong produces a zero that looks exactly like absence.
- No freight or forwarding entries in this release, by request; that section is unchanged.
- bump 0.7.0 to 0.7.1. Gates: `dash_guard`, `pii_guard`, `data_boundary` clean; `load_budget` ok; `verify_matrix` PASS; 4/4 test suites pass.

## [0.7.0], 2026-08-19

**The refresh that re-verified every row and still got the answer wrong.** `reference/data/README.md` had said for months that cross-border de-minimis "must be re-verified against the primary government source on every refresh, never from memory." That sentence was an intention with no mechanism. `cross-border-duty.json` then sat two months past its refresh still describing **IEEPA as live US tariff authority**, months after the Supreme Court had struck that authority down, while `verify_matrix` printed a clean DATA section on every single run. The gate asked whether `last_verified` EXISTED, and whether it was in the FUTURE. **Nothing ever asked whether it was OLD.** A gate that reassures is this fleet's signature defect, and this one had been reassuring since June.

The harder half is that a TTL alone would not have saved it. The 2026-06 refresh **did** run, row by row, and still shipped a file describing an abolished instrument, because every row re-verified cleanly against its own Federal Register notice, and that notice is still online and still says exactly what it said the day it was published. **Row-level re-verification can only ever confirm that a source has not changed its mind.** A repealed, expired, enjoined, or struck-down instrument leaves rows that are individually verifiable and jointly wrong. So the file now leads with a framework row naming which instruments are in force, and the refresh protocol asks that question before it asks any rate.

- **NEW freshness gate: every data table declares how fast its own facts rot.** `review_cadence_days` is a required envelope key. Past 1x the declared cadence WARNs, past 2x BLOCKs, and a table that does not declare a cadence BLOCKs outright, because a table with no declared rot rate can never be reported stale, which is precisely how this file class went wrong. One global TTL would be wrong in both directions: statutory sales-tax rates move about once a year, while the 2026 US tariff regime moved three times in eight months. Current values: `cross-border-duty` 45, `shipping-baselines` 180, `us-sales-tax` 365.
- **Two silent-skip bugs found next to it, both fail-closed now.** (a) The old `last_verified` check read `if mlv and <future test>`, so a stamp that did not parse made `mlv` None and **skipped every freshness assertion while the file printed clean**; an unageable stamp is indistinguishable from one never verified, and now BLOCKs. (b) The whole DATA section was wrapped in `if os.path.isdir(DATA_DIR)`, with a comment admitting it was a temporary green "until the parallel agent lands the directory". The directory landed; the temporary green became permanent. Deleting or renaming `reference/data/` made every check below it vanish and the gate report success. Finding nothing to measure is now a BLOCK, same reasoning `load_budget` already documents for exit 3.
- **Freshness logic extracted to `verify_matrix.check_data_freshness()`, a pure function, with `tools/test_data_freshness.py` (16 cases) wired into `gate.yml`.** It is kept out of `run_checks()` deliberately: `run_checks()` makes GitHub round-trips, so testing date arithmetic through it would burn API quota to assert local arithmetic. Half the cases are **negative controls** that assert the gate FIRES (malformed stamp, month 13, `true` masquerading as an integer cadence since `bool` subclasses `int` in Python, zero and negative cadences, future stamps), plus a positive control asserting a fresh file stays silent, because a suite that only ever asserts silence cannot tell "nothing wrong" from "not looking". The CI step carries the same file-existence guard the pii-guard workflow uses: a guard that is not here is not a guard.
- **`cross-border-duty.json` re-verified from primary sources and restructured, 16 rows to 29.** Verification ran as five independent researchers followed by five adversarial skeptics briefed to refute rather than agree; three of five findings came back flagged unsafe to write as stated, and the corrections below are the reason that layer exists.
  - **NEW framework rows, placed first**: which instruments are in force (Section 301 China Lists 1-4, Section 301 forced labor, Section 232, AD/CVD), and explicitly which are dead (**all IEEPA tariffs since 2026-02-24**, the **Section 122 10 pct global surcharge since 2026-07-24**). IEEPA fell in *Learning Resources, Inc. v. Trump*, No. 24-1287, consolidated with *Trump v. V.O.S. Selections*, 607 U.S. 229 (2026), decided 2026-02-20 6 to 3; EO 14389 terminated the duties and CBP CSMS #67834313 stopped collection.
  - **The de-minimis suspension SURVIVED, and the reason inverts the obvious risk model.** It looked like collateral damage waiting to happen, since EO 14324 was IEEPA-based. It is not: EO 14388 rests on 50 USC 1702(a)(1)(B), the power to nullify the exercising of a privilege, which is not the tariff power the Court rejected, and CBP's two interim final rules of 2026-06-24 state verbatim that CBP acts independently under its own statutory authorities, giving the suspension a second leg that does not depend on IEEPA at all. The CIT upheld it on 2026-08-13. **A US consumer still cannot receive a commercial sub-$800 parcel duty free.**
  - **The new forced-labor Section 301 has FOUR tiers, not two, and coding it as a uniform add-on corrupts landed cost.** 10 pct flat (17 economies), 10 pct **net of MFN** (EU, Taiwan), 12.5 pct **net of MFN** (Japan, South Korea, Switzerland), 12.5 pct flat (38 economies). In the net-of-MFN tiers the duty is only the GAP, so MFN plus 301 equals the tier rate. **Japan is the trap**: it reads as exempt from a two-tier summary, and a Japan-origin good whose Column 1 rate is Free still lands at 12.5 pct, not 0.
  - **NEW rows for the mechanics that actually decide a number**: origin is where a thing was MANUFACTURED and never where it shipped from (so a Thailand-built item sent from China does not pay the China List 3 duty); List 3 maps `9002.11.90` to `9903.88.03` at +25 pct per the USITC concordance rather than any summary site; `hts_camera_lens_9002_11_90_00` at 2.3 pct with the note that program code A (GSP) has been lapsed since 2020-12-31 and is not claimable; and a watchlist of four pending actions (a second 301 on excess capacity covering China, Thailand and Japan; the China 301 four-year review; UAS Section 232 effective 2026-09-03; drawback disallowed from 2026-08-12) which is the concrete reason this table carries a 45-day cadence rather than a comfortable one.
- **NEW channel class, offer-brokerage / name-your-price** (`channel-classes.md`), surfaced by the operator rather than by triage, which is itself the finding: it was unenumerable because no row described it. It is the only channel that legitimately transacts **below MAP with the full manufacturer warranty**, because MAP binds the *advertised* price and not the transacted one, and it therefore exists in exactly the categories where every visible retailer quotes an identical number and a run looks finished at that number. Three rules ship with it. Its own "lowest online" comparison table is an **affiliate placement** subject to guardrail #10, observed citing a first-party retailer $300 under that retailer's live price on a link carrying the broker's own affiliate tag. An offer is a **firm, irrevocable commitment** that auto-charges on acceptance, with a restocking fee the accepting retailer sets, so **this class cannot be taken to E1 without spending the operator's money**: a named broker plus a calibrated offer band plus the commitment caveat IS the covered state, and per CONSTITUTION V.4 the agent never submits the offer.
- bump 0.6.0 to 0.7.0. Gates: `dash_guard` clean, `pii_guard` clean, `data_boundary` clean, `load_budget` 0.82 pct, `verify_matrix` PASS, 4/4 tool test suites pass.

## [0.6.0], 2026-07-29

**The login handoff, the third access state.** The matrix modelled every source as two-state: anonymously readable, or unavailable. Real consumer marketplaces have a third state, and it is the one the operator cares most about: **session-gated**, fully readable the moment a human logs in once, returning nothing at all until then. With no vocabulary for that state the skill did the only thing it could and filed the channel as a permanent `coverage_gap`, while the person who wanted the answer sat right there and could have opened the door in ten seconds. A real run spent eleven keyword retries and about an hour of wall-clock re-discovering that a C2C marketplace was walled, then reported it as unreachable. That is not a coverage limit. It is **a handoff that was never designed**, and this release designs it.

- **NEW `reference/login-handoff.md`, and a NEW Step 3b + Step 5b in SKILL.md.** Every in-scope channel now gets an access state: **S1** anonymous, **S2** session-gated, **S3** structural (geo-block, dead domain, closed API, proxy pool). S2 is **never** a gap until the operator has been asked. The handoff itself is blocking and deliberately shaped: finish all S1 work first so a refusal still ships a full report; **batch every gated channel into ONE ask**; open the login page and **stop emitting tool calls**; state what each platform unlocks; give a resume signal; **end the turn.** Waiting means ending the turn, not polling in a loop.
- **The agent never authenticates (CONSTITUTION NEW V.4).** No usernames, passwords, SMS or TOTP codes, QR scans, or account creation, even if the operator pastes a credential into the transcript. A post-login page is also a **PII surface**: snapshots are scoped to product content, never account, order-history, address-book, saved-payment, or messaging views, which extends V.3 from API keys to session PII. Post-login access is **read-only**: no order, bid, offer, message, or settings change without a fresh per-action instruction, and a cart added to reveal a tax line must be emptied and re-read. A persisted session file is a bearer credential and lives outside any tree that is committed or backed up, by construction rather than by scanning, because `data_boundary` cannot tell a cookie jar from a fixture.
- **NEW guardrail #11 + CONSTITUTION II.7, the control query.** This is the trap that makes S2 dangerous rather than merely inconvenient: a gated marketplace search does not error, it renders its shell, its filters, even a recommendation carousel, and reports **"no results"**, which is byte-identical to "nobody sells this." Before any zero-result from a marketplace search is recorded, a **control query** for a term that platform certainly stocks must run; if the control also returns zero, **every zero from that platform that run is void** and is an access-state signal, never a stock signal. Three agents in the run that motivated this only avoided the wrong conclusion because each independently invented the control query. A guardrail beats a lucky habit. Loading the homepage first to collect a full risk-control cookie set was observed to change nothing and does not substitute.
- **Gap reasons are typed (guardrail #9c + CONSTITUTION II.8), and the report template carries the table.** One of `session-gated-declined` / `session-gated-unattended` / `structurally-unreachable` / `tool-outage` / `not-attempted`. "One login away" and "no login helps" are different facts that were collapsing into one bucket, which is precisely what made a reachable channel look permanently dead and misdirected the next refresh. Gapped cells are also never backfilled with another channel's numbers.
- **NEW channel class, C2C / social secondhand**, the class that kept getting written off. It is distinct from auction-house and consignment resale (the seller is an individual), it is frequently the only channel carrying a discontinued or region-exclusive item at all, and it is **S2 by default**. `channel-classes.md` now also states that in-scope-ness and access state are two different axes.
- **Browser concurrency is now a documented constraint, not a surprise.** The browser MCP is commonly **one shared instance across every subagent** whatever the isolation flags claim; observed with eight parallel agents, tabs stolen or closed under each other more than a dozen times. Recorded in SKILL.md Step 5 and `source-reliability.md`: atomic `newContext()`/`newPage()` per call is what survives, index-based tab addressing is not, **heavy in-page JS evaluation deadlocks silently until the MCP idle timeout** (tens of minutes, zero output), and a login handoff **cannot** run inside a parallel subagent because a sibling steals the tab mid-login. Gated work serializes into the main session.
- **`reference/source-reliability.md`, one entry reversed and several added.** The "Login-walled marketplaces are structurally unreachable" entry was itself the bug and is rewritten to S2. Added: the wall now reaches search and the PDP, not just checkout; **search engines do not index gated commerce PDPs**, so the find-it-on-a-SERP-then-open-the-URL bypass does not exist for this class (it works for content sites and systematically fails for commerce); forwarding/daigou agents are not a read bypass and may not support a retailer at all, though their **freight calculators are often anonymous**; price-history sites can inherit the wall; auction sold-comps have moved from open to gated, so "sold comps are free" is an expired fact.
- **Cross-border gains the oversized-goods rules.** **Volumetric weight, not actual weight, sets the freight**: for any edge over ~30cm compute `L x W x H / divisor` before quoting, because a large hollow item bills at 3 to 5 times its actual weight and freight can exceed the item price. Divisors differ per carrier **and per service on the same carrier** (5000/5500/6000/8000 observed side by side), so read the carrier's own. Small-parcel intuition understated a real quote by 30% to 100% in the motivating run, twice, in two different directions. **Box dimensions are a first-class landed-cost input** and usually appear only on a retailer PDP; two plausible box sizes swung one freight quote by 2x, enough to reorder the ranking. **Sea freight is routinely cheapest by a wide margin** for bulky low-value non-urgent goods and is often absent from forwarder marketing; a forwarder's rate API may be **anonymous even when its product pages are not**, so a route can be priced exactly while the purchase path is unavailable, and its internal FX rate can add a spread on top.
- **Tariff schedules: verify list membership against the primary schedule, never a summary.** Two independent tariff-summary sites returned two different rates for the same category and **both were wrong**: the goods were on no active list, because the list containing them was announced and then suspended before ever taking effect. Secondary sites do not model "announced but never in force." Parsing the customs authority's own published mapping settled it.
- **NEW guardrail #12, the first page is not the market.** #11 stopped a zero-result being read as "nobody sells this"; it did nothing about reading only the top of a non-zero one, and the two are the same disease. Any "cheapest" entering the ranking must now declare its **search depth** (pages read, unique items, how paging was driven), and pages are judged by **new ids, never by returned count**. All three paging mechanisms were observed in one run: a working URL page param; a **URL page param silently ignored while still rendering a full grid of page-one rows**; and paging that only advances by clicking numeric controls. **Trusting an ignored page param is worse than not paging at all, because it manufactures false coverage.** Depth payoff is unpredictable and must be measured, not assumed: the same query went 30 to 270 unique items on one marketplace (surfacing a lower floor) and 46 to 47 on another.
- **The guardrails are reorganized into five questions** (provenance / comparability / verification / absence / adversarial) with a routing table at the top. Twelve flat rules had grown past the point where a reader could tell which ones were about the same failure, and four of them (#6, #9, #11, #12) turn out to be one idea: **a rendered result grid looks identical whether the market is empty, the query was gated, or you only read the top of it.** They now sit together under that sentence. **Numbered IDs are deliberately NOT renumbered**, because `evidence-schema.md`, `report-template.md` and the CONSTITUTION cite them; the grouping is presentation, the IDs are the contract.
- **`reference/source-reliability.md` consolidated rather than extended.** The old "a verified ZERO is a finding" entry is absorbed into a new **"Reading a search result page"** section built around a four-row table (rows/no-rows x real/artifact), which is where the paging and broken-endpoint failures also belong. A second new section, **"What a listing page says versus what is true"**, collects the claims a PDP makes that are not true: a structured in-stock attribute contradicted by the listing's own preorder text; reseller spec blocks copy-pasted from a sibling product (a 400mm item declared 40mm, wrong character, 1/1 scale on a 1/12 piece, one page); a SKU hidden inside a multi-SKU collection whose title names other products entirely, which is how a brand flagship can look like it stopped selling something it still sells cheapest; and promotions, where **a PDP lists what exists and only the order-confirm page shows what stacks**. The overlapping "used-listing titles misstate the spec" bullet is merged rather than duplicated.
- **A brand's own in-store search can be the broken thing.** A legacy per-shop search endpoint ignored its keyword parameter entirely and served the byte-identical empty state for every term, while the shop's full catalogue sat behind its all-products listing. Believing it inverts the conclusion. Same family as the parameter-naming trap (`query1=` works, `query=` returns zero): the site is healthy, the URL is wrong, and only a control query separates that from out of stock.
- **#5 gains a second purpose.** Reading Sold-by was framed purely as a trust gate; it is also **channel discovery**, since a third-party seller on a big-box domain can be the product's own exclusive source, whose first-party storefront sells the same unit for less.
- **`variant_key` is now stated as a provenance field with its own evidence rule**: confirm from spec text, SKU option strings, or a manufacturer id, never the title; when a spec block and an option string disagree, the option string wins and that spec block stops counting as an independent source.
- CONSTITUTION NEW **II.6, II.7, II.8, V.4**. Per CONSTITUTION VII these are a reasoned change routed to human review, not a refresh sweep; `verify_matrix` flags the baseline diff by design.
- bump 0.5.0 → 0.6.0. Gates: `dash_guard` clean, `data_boundary` clean, `pii_guard` clean.

## [0.5.0], 2026-07-13

**Data boundary, the skill stops writing its user's life into a public repo.** `metrics/live-runs.jsonl` was git-tracked and append-only: SKILL.md Step 7 told every real run to add one line per source touched. It worked exactly as designed, and what it accumulated was a shopping history, which products got priced, which retailers got bought from, which region they ship to. **`pii_guard` passed it clean on every commit**, because there is no email or phone in a domain slug. That is the whole lesson of this release: a content scanner is a sieve at the exit, and it cannot see a leak that is merely *someone's life, correctly formatted*. The fix is not a better sieve, it is a pipe that does not point at the public repo.

**A public skill repo is now an UNINITIALIZED TOOL.** Every path belongs to one declared class (NEW `.dataclass.json`): TOOL (code + docs), FIXTURE (synthetic), DATA (anything a real run produced, private, never tracked, published only as a schema).

- **DATA moved out.** `metrics/live-runs.jsonl` + `metrics/gh-api-cache.json` now resolve from the private companion config (`~/.shopping-aggregator-config/data/`, or `$SHOPPING_AGGREGATOR_DATA_DIR`) via NEW `tools/datadir.py`. **There is deliberately no in-repo fallback path**, a fallback into the repo is not a convenience, it *is* the leak (a sibling repo's real contact email was committed through exactly such a documented "legacy fallback"). Uninitialized, the tools raise `DataDirNotInitialized` with setup instructions. History rewritten with `git-filter-repo`: the 28 real observation lines are gone from every commit, not merely deleted at HEAD.
- **NEW `metrics/live-runs.jsonl.example` + `metrics/gh-api-cache.json.example`**, the shape, with synthetic contents. An uninitialized tool still has to be a *usable* one, and the schema is all a fresh clone knows about the lines it must produce.
- **NEW `reference/source-reliability.md`, the tool knowledge, kept.** The 28 private lines contained something genuinely generalizable, and throwing it away would have been the other way to get this wrong. Distilled by hand into route-reliability facts stripped of product, price, and region: model-summarized prices (cross-model `web_search`, SERP snippets) run systematically *below* live authorized listings → `L5` leads, never ranked; **BigGo returns ZERO for niche SKUs and empty ≠ unavailable** → fall back to a direct scrape before concluding a product has no listings; JS-rendered PDPs scrape as **`$0`, which is a failed read, not a price** → detect the signature, fall back to category/SERP + history, mark `E2`; big-box domains host 3P marketplace sellers, so a conspicuously cheap listing needs the Sold-by/Shipped-by read *before* ranking; pickup-only chains key stock **per store**, so the national page is a query you have not run yet; login-walled social marketplaces are a *structural* coverage gap; a verified ZERO is a finding, and is not the same as a gap.
- **NEW `tools/data_boundary.py`, wired into both hooks and CI**, asserts no DATA path is tracked, that each still ships its schema, and that every FIXTURE is byte-identical to its generator's output. It runs **before** `pii_guard`, which is demoted from primary control to backstop: the class declaration catches what the content scan structurally cannot.
- **NEW `tools/make_fixtures.py`, `reference/scenario-eval/scenarios.jsonl` becomes a GENERATED FIXTURE.** Its contents are **unchanged** (same 7 scenarios, same reference SKUs, byte-identical); only the source of truth moved into a case table + a `REFERENCE_SKUS` constant table that every `buy_intent` is rendered from. It was clean, and that is exactly why it was the most dangerous file here: its rows are realistic shopping intents naming a real product shipped to a real place, and the most convenient realistic example available to the next agent is *what the operator actually bought*. Such a row would look completely at home, would pass review because it is indistinguishable from its neighbours, and **a content scanner cannot catch it, a product name is not a PII pattern.** Demonstrated: pasting the operator's real purchase (no ZIP, no email, nothing that "looks private") into the fixture leaves `pii_guard` **clean, exit 0**, while `data_boundary` **BLOCKS, exit 1**. A real purchase cannot be regenerated. Docs repointed so the next agent adds a CASE, not a line: `judge-protocol.md`, `tools/scenario_eval.py`.
- **`tools/refresh_priority.py`**, reads the private file, resolved **lazily** (a `_LazyPath` for the argparse default) so a fresh clone still imports cleanly. Exit **2** = no data dir = uninitialized, which is a state, not a failure.
- **`tools/verify_matrix.py` LIVERUNS**, now BLOCKs on the published `.example` schema (present + valid + 6 required keys), and additionally validates the operator's real private file when the machine has one. A fresh clone checks only the schema, and passes.
- **CONSTITUTION II.5 rewritten + NEW II.5a**, observations MUST go to the private dir and MUST NOT be written into the repo; the generalizable half MAY be distilled into `source-reliability.md`. **If the lesson cannot be stated without naming what was bought, it is not yet a lesson.** (II.5 previously said "when the repo is checked out and the file is writable", it *mandated* the leak.)
- **Docs repointed:** SKILL.md Step 7 + progressive loading, `reference/refresh-protocol.md` (×4, plus a new "then distil" step), `reference/scenario-eval/judge-protocol.md`, ROADMAP. `.gitignore` ignores the DATA paths, allows the `.example`s.
- bump 0.4.1 → 0.5.0. Gate: PASS.

## [0.4.1], 2026-07-06

**Hotel/travel domain (minimal), matrix 12 → 13.** Adds the first lodging capability as ONE new domain shard + the smallest possible wiring: no new data tables, no new tool docs, no new registry entries. Flights / rental cars / trains explicitly OUT of scope (future extension).

- **NEW `reference/domains/hotel-travel.md`**, hotel/lodging price compare + book-to-confirm. **Booking.com ④ playwright is the spine** (tested search / result-card / `#hprt-table` room-table / `secure.booking.com/book.html?...&stage=1` Your-Details selectors captured verbatim, with a `browser_snapshot` fallback since Booking churns its DOM); **Google Hotels ④ is discovery-only**, its `ts=`/`qs=` URL locks the dates and the on-page date picker doesn't reliably apply, so trust it for *relative channel ordering* only, never its date-specific numbers; brand-direct (Hilton/Marriott/IHG) only beats OTA parity with a loyalty MEMBER rate → **with no membership, Booking is typically the lowest legitimate channel** (single-session illustrative ladder: Homewood Suites Booking $152 < Hilton official ~$163 < Expedia/Hotels.com/Priceline ~$175, re-priced live every run). The landed-cost analog is **total-stay cost** = nightly×nights + lodging/occupancy tax + cheapest parking + resort fees − discounts; **Booking's Your-Details Total is already tax-inclusive** (the `(NN% Tax)` line is a breakdown to READ, not an amount to add, no double-counting), the tax is **READ off the live page, never hard-coded** (honors guardrail #3 / CONSTITUTION I.7; the live-read line carries snapshot_ts + source_url so it stays auditable); **parking is NOT in Booking's total and materially reorders rankings** ($152 room + $20 self-park beats $150 + $55 valet), researched separately via SpotHero/ParkWhiz/hotel site. Refundable vs non-ref are DIFFERENT SKUs, surface both. **HARD operating rule:** drive to the "Your Details" confirm page, surface total + tax + cancellation + parking, then STOP and hand off name/payment, NEVER enter payment/PII (standing agent-configures / hand-off-at-payment principle).
- **Wiring:** `hotel-travel` row appended to `reference/sources-index.md` main table (barrier route ④); SKILL.md description triggers broadened (hotel/lodging + 订酒店/差旅住宿/酒店比价, 差旅 narrowed to 差旅住宿 so travel-planning/reimbursement asks don't misfire) with every product trigger kept; Step 2a gains a one-line hotel-routing note (tax read-not-hard-coded + separate parking; shard owns the full formula) and the domain count bumped 12 → 13; Scope section reconciled to admit lodging book-to-confirm (stops at payment hand-off, still the decision-layer identity).
- **Coupled updates (applied same commit):** `reference/channel-classes.md` gains a **travel-booking / OTA** class row + its X1-map row naming `hotel-travel` as the primary shard, and its Last-verified bumped 2026-06 → 2026-07; README.md + README_CN.md `12 domains` counts and shields badges → 13 plus a hotel-travel source-matrix row in each; `.claude-plugin/plugin.json` 0.4.0 → 0.4.1 (+ its description domain list). NO `tools/registry.json` / `tools/index.md` change, channels are a tool-only axis and no MCP/tool was added.
- bump 0.4.0 → 0.4.1. Gate expected PASS after the coupled plugin.json + channel-classes.md edits (both applied here); re-run the gate to confirm green before merge.

## [0.4.0], 2026-06-22

**Self-evolve round**, the single largest batch since v0.2.0. Run as parallel specialist subagents (data-tables / shards / tool-docs / gate-port / refresh-automation / scenario-eval) with a serial integrator finalizing version + docs + CI. Closes the entire v0.2 enforcement gap, the v0.4 domain expansion, and the landed-cost data gap at once. Matrix **9 → 12 domains**, tool docs **22 → ~32**, gate **6 → ~18 checks**, and the skill gains its first source-cited landed-cost data layer.

**Landed-cost data tables (NEW `reference/data/`).** Four source-of-record tables on a shared envelope `{schema_version, last_verified, rows:[{source_url, verified_date, evidence_grade, ...}]}`:
- **`us-sales-tax.json`**, per-US-state sales-tax rows (each cited to the state DoR). Landed-cost compute no longer hard-codes "(NJ rate assumed)."
- **`cross-border-duty.json`**, de-minimis thresholds + typical-category HTS duty rates, US↔CN/EU. **Highest-volatility facts in the repo.** Captures the post-2025 reality: **US §321 de-minimis SUSPENDED for all countries** (EO 14324, eff 2025-08-29; statutory repeal 2027-07-01), EU EUR-150 relief → **EUR 3 flat duty** from 2026-07-01, CN postal allowances. Web-verified this round against Federal Register 2025-16802 + CBP CSMS #66065494 + EU Council 2026-02-11 (all E1).
- **`shipping-baselines.json`**, carrier/forwarder baseline shipping bands.
- **`fx-source-of-record.md`**, names the dated, free FX rate source the harness reads (values fetched live, not cached).

**3 new domain shards (matrix 9 → 12), wired into every discovery surface.**
- **`reference/domains/auction-resale.md`**, resale/used value: eBay Sold SERP ④ free (`LH_Sold=1`), StockX Public API v2 ① (approval-gated), playwright ④ for GOAT/Whatnot/Poshmark/Mercari/Depop/ThredUp. Different trust model from new-retail.
- **`reference/domains/grocery-cpg.md`**, groceries/CPG: Flipp ① circular discovery + banner-app ① loyalty truth (Kroger fuel points, Target Circle, ShopRite Price Plus, Wegmans, Costco Executive), playwright ④ for live Instacart cart. Hyper-regional, pin ZIP→banner first.
- **`reference/domains/cross-border.md`**, 海淘/代购/forwarders: Superbuy/Stackry/MyUS/YesStyle ④. **Duty by default**, de-minimis suspended; all figures live in `reference/data/cross-border-duty.json` (CBP / Federal Register / EU Council primary, E1).
- **Wiring:** 3 rows added to `reference/sources-index.md` + both README source matrices; Domains badge **9 → 12**; a **Flipp grocery hand-off** note spliced into `mobile-apps-aggregators.md` (Flipp stays discoverable there, grocery mechanics route to `grocery-cpg.md`); the `12 domains` count bumped across README/README_CN/SKILL.md.

**Tool docs 22 → ~32.** Added per-tool how-to docs (install + auth + usage + 踩坑) for the documented-but-undocumented gaps: Bright Data, DealNews, InvisibleHand, RetailMeNot, Cently, 京东价保 (jd-price-protection), Slickdeals, reddit-deals, ScraperAPI, AliExpress, Xiaohongshu, and more, each with a registry + index row (THREEWAY stays consistent).

**Gate: market-intel's RICHER judgement checks ported (`tools/verify_matrix.py`, 6 → ~18 checks).** On top of the original deterministic 6 (THREEWAY/FRESH/TEMPLATE/VERSION/RENAME/LIVERUNS): **REPO** (repo existence, 404→BLOCK), **STAR** (★-claim tolerance), **GHACTIVE** (archived/stale push, cached 7d), **DOCCOVER** (live shard repo with no per-tool doc), **STALE** (tool doc >9mo unverified), **COVER/CHURN/DELETE** (git-baseline anti-mass-deletion + rewrite + death-code discipline), **CONST** (CONSTITUTION scope guard), **METH** (SKILL.md keeps the tier/grade legend + ≥10 guardrails). NEW checks added beyond the port: **DATA** (data-table envelope + per-row `source_url`/`verified_date`, future-date BLOCK) and **NOHARDCODE** (a tax/duty number in SKILL.md prose with no `reference/data/` citation and no `(assumed)` stamp → WARN, per CONSTITUTION I.7) and **SHARDSYNC** (a net-new shard must be registered → BLOCK). Network gates honour `--no-net` for offline CI; fail-closed on any uncaught error.

**Refresh + eval automation.** NEW `tools/refresh_priority.py`, deterministic weighted ranking of `metrics/live-runs.jsonl` problem events (`user_correction` 100 / `dead` 10 / `price_mismatch` 5 / `coverage_gap` 3); one definition shared by the refresh-protocol and the gate, replacing the old hand-run `jq | sort | uniq -c`. NEW `tools/scenario_eval.py`, fixture-driven scenario evaluation harness.

**`reference/refresh-protocol.md`, data-table staleness hook.** Every refresh sweep MUST re-confirm the four `reference/data/` tables against their cited primary source and bump `last_verified`, a green DATA shape-check is NOT permission to skip the fact-check. **De-minimis / cross-border duty = mandatory CBP-primary re-check on EVERY sweep** (most volatile + highest blast radius; a wrong de-minimis status silently mis-prices every cross-border landed cost). Adds per-table re-verification guidance for sales-tax / FX / shipping.

**Docs + version.** docs: unify repo structure (Skill Repo Spec v1), README/README_CN re-ordered to the philosophy-first section order (philosophy → what-it-is → install → quick start → how to invoke → example output → limitations → languages → roadmap), top badge block normalized to the standard order/colors, CN sections kept 1:1 with EN. `ROADMAP.md` restructured, completed work moved to a **Shipped** section (v0.4.0 self-evolve + earlier), stale "RICHER checks not ported" / "more tool docs (currently 22)" / "tax tables" claims removed as now-done; remaining roadmap is v0.3 loop-closing + v0.5 packaging. README/README_CN badges: **Tool docs → ~32 per-tool**, NEW **Data tables** badge (tax | duty | FX | shipping); Status sections de-staled. `.claude-plugin/plugin.json` bump **0.3.3 → 0.4.0**. Gate: **PASS** (`python tools/verify_matrix.py --no-net`, exit 0).

## [0.3.3], 2026-06-17

Documentation-consistency sweep (no skill-logic change). Grep-audited the whole repo for stale version strings, wrong counts, broken links, and pre-0.2.0 feature descriptions; only the two READMEs were stale.
- **`README.md` + `README_CN.md`**, version badge 0.1.0 → 0.3.3; fixed a broken **doubled `SKILL.md` link** (`skills/shopping-aggregator/skills/shopping-aggregator/SKILL.md` → `skills/shopping-aggregator/SKILL.md`); rewrote Status/roadmap to reflect what shipped since v0.1.0 (channel-class primitive, seller_tier+evidence_grade split, variant_key, coverage floor, CONSTITUTION, codex-crossval, the executable gate), corrected tool-doc count **17 → 22**, re-scoped remaining gaps to market-intel's richer judgement checks; added the new headline guardrails (evidence-grade-gates-ranking, seller-identity-not-domain, variant pinning, coverage floor) to the guardrails list and the channel-class mapping to the intent-parse step.
- Verified the rest is NOT stale: ROADMAP / refresh-protocol / CONSTITUTION / PHILOSOPHY / shards already current as of 0.3.2; remaining `source_tier` mentions are the gate's own definition (exempt) + the live-runs genesis line (historical record); the two `guardrail #5` shard refs correctly point to seller-tier (genuinely #5).
- bump 0.3.2 → 0.3.3. Gate: PASS.

## [0.3.2], 2026-06-17

Structure-audit cleanup. A 6-lens structural audit returned **MINOR-ONLY (leaning CONVERGED)**, the architecture is sound (thin layer, layered-DRY canonical-home+pointer, scoped gate, no orphans/double-homing; DRY lens converged outright). Landed only the 3 genuine items + doc-honesty; explicitly did NOT re-open structure (no new shards, no SKILL.md re-split, no brittle gate checks, those were named churn/net-negative).

- **`reference/refresh-protocol.md`**, flipped an operationally-live falsehood: it told a refresh-sweep agent the skill "does not yet have its own gate (planned)", but the gate shipped in 0.3.0. Now states it ships `tools/verify_matrix.py` + `gate.yml` (6 checks); market-intel's richer judgement checks remain the gap.
- **`tools/verify_matrix.py`**, added a 6th deterministic check **LIVERUNS**: `metrics/live-runs.jsonl` (consumed by the refresh loop), every non-blank line must parse as JSON + carry the 6 required keys (BLOCK); `outcome` in the declared set (WARN). A corrupt metrics file no longer silently breaks the refresh loop.
- **`SKILL.md`**, Step 4: made the shardless-channel-class path explicit (brand-direct / cross-border / non-PC category-specialists have no domain shard → run them directly via the channel-classes route; do NOT create shards). Progressive-loading block: added `channel-classes.md` (a triage-tier load that was omitted).
- **`ROADMAP.md`**, version → 0.3.2; checked off the now-shipped gate bullet.
- bump 0.3.1 → 0.3.2. Gate: PASS (6 checks). README version/count refresh deferred (human-only cosmetic). **Structure declared converged, stop.**

## [0.3.1], 2026-06-17

Iteration-loop round-1 cleanup. A 4-lens review of 0.3.0 CONVERGED (4/4 lenses converged, zero critical/major regression, the restructure dropped no rule, all evidence-schema.md pointers resolve, the gate is genuine enforcement). These are the residual minors it surfaced:
- **`reference/report-template.md`**, the ranking-table note pointed the "only an E1 row may be #1" rule at guardrail #5, but the 0.3.0 split moved that rule to **#5b** (#5 is now seller-tier). Fixed.
- **`SKILL.md` Step 3**, two in-prose pointers (`domains/amazon-us.md`, `tools/biggo-mcp.md`) were missing the `reference/` prefix every other pointer in the file uses → would mis-resolve for an agent following them verbatim. Fixed.
- **`tools/verify_matrix.py`**, THREEWAY docstring clarified as EXISTENCE-only (per-domain placement is advisory, not gated), removes a slight overclaim.
- bump 0.3.0 → 0.3.1. Gate: PASS.

## [0.3.0], 2026-06-17

APPRAISAL-driven batch from an honest 6-lens self-evaluation of v0.2.0. Overall finding: the skill was 思路-correct but had written many advisory "MUST" rules with **NO executable gate** behind them, violating its own PHILOSOPHY P2 (mechanism, not intention), and `SKILL.md` (332 lines) had outgrown its thin always-loaded budget against the parent market-intel (299). This batch closes the P2 gap with the skill's first real gate, repairs a dead feedback loop, and slims the entry-point doc.

- **NEW `tools/verify_matrix.py` + `.github/workflows/gate.yml`**, the skill's **FIRST executable deterministic lint gate** (Python 3, run from repo root, exit 0 = PASS / non-zero = BLOCK, fail-closed). Five non-judgemental artifact/contract checks adapted from market-intel's gate, trimmed to only the deterministic ones: (1) **THREEWAY**, `registry.json` slugs ⟷ `reference/tools/<slug>.md` files ⟷ `index.md` rows (registry slugs de-duped first, since biggo-mcp/manmanbuy/smzdm appear once per domain), BLOCK on mismatch; (2) **FRESH**, every `domains/*.md` + `tools/*.md` must carry a `last_verified` / `Last verified:` line (WARN, by design, a rot signal, not a broken contract, and durable while prose is restructured); (3) **TEMPLATE**, `report-template.md` must have a `Coverage gaps` heading (CONSTITUTION I.6) AND an `Ev` column in the ranking table (I.3), BLOCK; (4) **VERSION**, CHANGELOG top version == `plugin.json` version, BLOCK on mismatch; (5) **RENAME**, the snake_case token `source_tier` (renamed to `seller_tier` + `evidence_grade` in 0.2.0) must not leak in any `.md` under `skills/`, BLOCK. CI runs `python tools/verify_matrix.py` on push + pull_request. This turns the advisory structure into a **checked mechanism**, the central appraisal finding. Gates only durable contracts/artifacts (no prose line numbers, no guardrail numbering) so it survives prose restructuring.
- **Feedback loop backfilled (live-runs metrics)**, the file was **empty**, so refresh-protocol's feedback jq depended on a dead file. Backfilled 7 honest one-line-per-source entries for the two documented real runs, each tagged `(backfilled 2026-06-17 from documented run)`: brightdata=verified, BigGo niche-SKU=`coverage_gap`, pickup-only-retailer missing-then-found=`coverage_gap`, big-box fake-first-party=`price_mismatch`, codex undershoot=`price_mismatch`. Genesis line preserved; all lines valid JSON. *(Redacted in 0.5.0: these observations are DATA and now live in the private data dir, see that entry.)*
- **`ROADMAP.md` de-staled**, rewrote the stale v0.1.0 heading to current 0.2.0 state (shipped CONSTITUTION / channel-classes / evidence-schema with `variant_key`+`seller_tier`+`evidence_grade` / seller-identity gate / codex-crossval); checked off the CONSTITUTION bullet; annotated the `verify_matrix.py` bullet as LANDING in this 0.3.0 batch; corrected the tool-doc count 17 → 22.
- **`reference/codex-crossval.md`**, canonical-call example `model_reasoning_effort` fixed `high` → `xhigh` to match the surrounding doctrine.
- **`SKILL.md` slimmed 332 → 249 lines** by moving the annotated evidence-unit schema + the long guardrail-#5/#5b/#7/#8/#9/#10 bodies + the two "Run B" war-stories into **NEW `reference/evidence-schema.md`** (read at Step 5); SKILL.md keeps a bare field-name schema + pointer. Step 2 split into **2a triage / 2b channel-class map / 2c depth budget** with a mandatory `[matched domains | in-scope channel classes | depth cap]` output line, channel-classes promoted to a first-class sub-step, `quick` (3/1/1) made the **default** with an honest 80/20 line, and ai-shopping-assistants added to the US enumeration. Guardrail #5 split into **#5** (seller tiers L1 to L5, read Sold-by) + **#5b** (evidence grade E1/E2/E3 gates ranking first, only E1 wins); #7 and #9 use (a)/(b) sub-bullets so the second obligation can't be missed. Added a 6-item **"before you emit the report" self-check** at the end of Step 6, and an explicit **zero-context verifier spawn** at the end of Step 5 (CONSTITUTION II.4). Removed the duplicate body "Base directory" line.
- **`CONSTITUTION.md` II.5**, softened to an honest-downgrade: live-run observations MUST be appended when the repo is checked out + writable; otherwise MUST be noted in the reply; dropping them entirely is a bug.

**Still advisory** (judgement-dense, not mechanizable): seller-identity reasoning, evidence-grade assignment, cross-source reconciliation cause-sets, channel-class matching, these remain MUST-prose because they require model judgement, not a regex. **Now enforced** (by `verify_matrix.py`): registry/index/tool-doc three-way consistency, freshness stamps (warn), report-template Coverage-gaps + Ev contract, CHANGELOG ⟷ plugin version sync, no `source_tier` leak.

## [0.2.0], 2026-06-17

STRUCTURAL / framework batch from a multi-round, 6-lens consensus reflection on WHY the skill kept missing tool-less channels (Micro Center) and produced internally inconsistent retrieval, root causes, not source expansion. Root causes found: (1) the only machine-readable artifact (`registry.json`) + the CONSTITUTION's consistency rules are TOOL-shaped, so a channel with no tool is structurally un-representable and invisible to triage/refresh; (2) discovery enumerates TOOLS, never MISSING CHANNELS; (3) a "price" was a scalar with no SKU-variant key, no evidence-provenance grade, no cross-source reconciliation, and coverage had ceilings but no floor. This batch upgrades those from prose intent to schema/guardrail MECHANISM (PHILOSOPHY P2). Owner decision deferred to ROADMAP: whether closing the coverage/reconciliation loop ultimately needs the skill's first executable lint gate (the fixes here are advisory / by-construction on already-enforced artifacts, since the skill has no gate yet).

- **NEW `reference/channel-classes.md`**, a DEMAND-SIDE channel-class primitive (mass-market · category-specialist · brand-direct · warehouse · local-pickup-only · cross-border · refurb), the counterweight to the supply-side tool matrix. Tool-less authorized retailers (Micro Center, B&H, Adorama…) are now first-class via the browser/scrape route. `SKILL.md` Step 2 maps the product to its channel classes; `sources-index.md` points to it. Root fix for "tool-less channel = invisible."
- **`SKILL.md` evidence-unit schema**, added `variant_key` (REQUIRED) and split `source_tier` into `seller_tier` (who sold it) + `evidence_grade` (E1 PDP/API · E2 aggregator · E3 snippet/lead). Guardrail #5: evidence_grade gates ranking FIRST and overrides seller_tier, only E1 may win, E3 is a lead never ranked (fixes the $1,450-snippet-as-price error). Guardrail #7 extended to cross-SOURCE reconciliation (same-variant_key, closed cause-set, resolve by E1>E2>E3, never average). Guardrail #9 added a coverage FLOOR, an in-scope channel class never attempted is a `not-attempted` gap that emits a `coverage_gap` line.
- **`CONSTITUTION.md`**, I.3 now requires seller_tier + evidence_grade; new I.3a requires variant_key (different variant = different SKU, never merged); I.4 tightened (the #1 rec must rest on ≥2 independent E1 reads of the same variant_key, no single-source escape for the winner); II.4 verifier must also confirm seller + evidence_grade for any E1/L1 winner.
- **`reference/report-template.md`**, ranking table gains `Variant (key)` + `Ev` columns (one row per variant_key); Sources lines carry an evidence-grade token; Disagreement matrix notes same-variant_key + closed cause-set + E1-wins.
- **`reference/refresh-protocol.md`**, Discovery gains a coverage-driven **channel-completeness audit** (not just tool hunting); feedback jq now prioritizes the new `coverage_gap` outcome (how a MISSING CHANNEL reaches the refresh loop) and corrects the `user_correction` orphan (it is a JSON key, not an outcome value); fixed a stale line that claimed no CONSTITUTION.md ships (it now does).
- bump 0.1.6 → 0.2.0. DROPPED as scope creep (per multi-lens consensus): per-retailer scraper/price engine; channels-in-registry.json; auto channel-discovery crawler; numeric confidence/reconciliation scoring; shard rename; a `channel_gap` synonym (reuse parent skill's `coverage_gap`); a new BLOCKING workflow step (the skill has no executable gate, so a BLOCKING step would be empty intent, the very P2 anti-pattern).

## [0.1.6], 2026-06-17

Skill-improvement batch (Tier 1) from a 9-agent skeptical evaluation of two end-to-end runs across different product categories (buyer details redacted in 0.5.0). Closes the three decision-grade misses those runs exposed. (Tier 2, a store-pickup `fulfillment` schema field + a single-page-overflow note, deferred to 0.1.7; `codex-stale-price-note` dropped as already-documented; `bounded-external-delegate` folded into codex-crossval.md as one generalizing line.)

- **`reference/domains/ebay-walmart-target.md`**, added **Micro Center** as a source (triage list + per-retailer gotcha): US authorized PC-parts retailer, **pickup-only + per-store stock**, must scrape the specific store page (storeid) for the buyer's ZIP; codex/BigGo miss per-store stock. The chain page showed nothing while the buyer's own branch page showed units on the shelf, findable only this way. Also extended the **Best Buy** bullet with the **Marketplace 3P** trap (a conspicuously cheap listing was a 3.7★ marketplace seller, not Best Buy first-party).
- **`SKILL.md` guardrail #5**, upgraded to a **seller-identity gate**: a retailer domain is not proof of first-party (Best Buy/Walmart Marketplace, Newegg/Amazon 3P all render under the retailer domain); **stamp L1 only after reading the `Sold by`/`Shipped by` field**; a missing seller_name **degrades to L3, never rejects** the unit (preserves codex/BigGo L5 leads). `seller_name` marked required-for-L1 to L4 in the evidence-unit schema. Mirrors the P2 mechanism-not-intention move already made for `snapshot_ts`.
- **`reference/domains/amazon-us.md`**, noted the **main Buy Box can be a 3P seller** (read "Ships from/Sold by"; only "Sold by Amazon.com"/brand store is L1).
- **`reference/tools/biggo-mcp.md` + `reference/domains/claude-mcps.md`**, corrected the falsified "OK for US" coverage claim to "OK for US mainstream; **weak for niche/US-specific SKUs**" (Run B: BigGo returned ZERO for a niche US GPU SKU); **an empty BigGo result ≠ unavailable**, fall back to Bright Data SERP + retailer scrape (P6 visible-degradation). Noted BigGo's `spec_search` suggestion is a spec lookup, not a price source.
- **`reference/codex-crossval.md`**, added one generalizing line: any external agentic delegate (codex today; future MCPs) is invoked with its browser/sub-MCP tools stripped + best-effort skip per guardrail #9.
- bump 0.1.5 → 0.1.6. No matrix/registry/tool-doc additions (Micro Center documented in-shard, not as a new tool primitive).

## [0.1.5], 2026-06-17

Harden the Codex cross-val back-end after a real **10.5-hour hang**. First live `mcp__codex__codex` run (a GPU price check, MCP tools not disabled) drove Codex's OWN playwright `browser_navigate` to an anti-bot retailer (Cloudflare), which hung with no timeout for **38,037 s** until the user aborted, NOT a network/auth problem (model calls succeeded, Pro plan, tokens counted). Root cause: the user's `~/.codex/config.toml` registers `[mcp_servers.playwright]`, so Codex tries to drive a headless browser to live retail pages (and collides with Claude's own playwright). 

- **`reference/codex-crossval.md`**, new **⚠️ CRITICAL** section: ALWAYS call `mcp__codex__codex` with `config.mcp_servers={}` (strips Codex's browser/MCP tools → web_search only) + `sandbox:read-only` + `approval-policy:never` + a prompt instruction to use only web_search. Verified 2026-06-17: same query then returned in <1 min. Reinforces the doctrine, Codex does web_search soft cross-val, NOT live-browser price fetch (that's this skill's Bright Data/playwright job). Empirical note updated with the incident + a cross-val data point (Codex's ~$1.0 to 1.3k undershot the live authorized $1.20 to 1.45k listings → why its prices are L5 leads).
- No SKILL.md / matrix / registry changes.

## [0.1.4], 2026-06-16

Add **Codex MCP as an optional cross-model cross-validation + channel-discovery back-end** (NOT a price source). Prompted by a user question + an empirical test: a different model (GPT) with its own web search is a genuinely independent second opinion for the *soft* layer (authorized channels, missed cheaper authentic sources, counterfeit reputation, cross-checking the cheapest pick), but unreliable for authoritative live prices on anti-bot retail pages, so its prices are **L5 leads** that must re-pass the live-fetch + citation gate before ranking. Doctrine: Codex is a delegation back-end like `deep-research` / `market-intel` (PHILOSOPHY P5), so it is documented under `reference/`, **not** added to `reference/tools/` or the source matrix / registry, no matrix/registry churn.

- **`reference/codex-crossval.md`** (new), how-to: why the MCP route not `codex exec` (the latter hits a `cloud config bundle` egress timeout in the agent sandbox; the `codex mcp-server` MCP route works, verified `✔ Connected` 2026-06-16), the `--search` vs `-c tools.web_search=true` gotcha, best model = newest (gpt-5.5 / xhigh, ChatGPT-subscription auth), the L5-lead rule, and how to fold results (re-verify new channels, surface divergences per guardrail #7, best-effort skip per #9).
- **`SKILL.md` Step 5**, added the Codex-MCP cross-validation / discovery delegate bullet (L5 leads, best-effort, MCP-not-exec).
- **`SKILL.md` guardrail #8**, the disconfirmation reverse-search may also run through the Codex MCP as an independent cross-model check (L5 corroboration).
- No tool / matrix / registry changes.

## [0.1.3], 2026-06-16

Sync to market-intel v0.12.0 spec change: `companion-config-spec` v1 now formally
recognizes two storage modes for a companion repo's secrets, Mode A (committed to private
repo, single source of truth) and Mode B (gitignored, out-of-band backup). The
shopping-aggregator install-guide's L3 row already delegates to market-intel's spec for the
formal contract; no shopping-aggregator-side doc changes required (the cross-reference
picks up the new section automatically). Bump for traceability only.

## [0.1.2], 2026-06-16

`install-guide.md` slimmed from 133 → 93 lines (30% smaller) by delegating L0 install
mechanics (prerequisites, MCP transport types, `claude mcp add` procedure, secret-handling
hygiene, Windows notes) to market-intel's authoritative install-guide via cross-references.

This eliminates the duplicated-content drift risk that surfaced in v0.1.1 (where the same
OS-clipboard command updates had to be made in two places). What remains in this file is
only what's specific to shopping-aggregator's tool mix: the four shopping-tool kinds
(MCPs, browser extensions, mobile apps, OSS self-host), user-side tool detection (extensions
the skill can't probe automatically), and the deviation list versus market-intel.

The companion-config-repo pattern reference now also points to market-intel as the canonical
spec; the same pattern works for a `shopping-aggregator-config/` companion if a user wants
to maintain Keepa subscription + browser-extension install state outside this matrix.

No tool/matrix changes.

## [0.1.1], 2026-06-16

- **`reference/install-guide.md`**, secret-handling hygiene now lists clipboard commands for
  all three OSes (PowerShell `Get-Clipboard`, macOS `pbpaste`, Linux `xclip -o`/`wl-paste`)
  rather than implying PowerShell. The "Windows notes" section retains PowerShell appropriately
  since it's the Windows-specific section.
- **`reference/refresh-protocol.md`**, "push to DaizeDong/shopping-aggregator" replaced with
  "push to whichever Git remote this skill repo lives at."

No tool/matrix changes. Forkability cleanup only.

## [0.1.0], 2026-06-15

Initial public release. Hand-curated matrix derived from a 5-subagent shopping landscape survey
done 2026-06-15 (US + CN consumer-shopping coverage), paired with patterns inherited unchanged
from `DaizeDong/market-intel` (philosophy, install-guide L0 mechanics, progressive-loading
discipline, refresh-protocol bones, plugin layout).

### Why this skill exists

The 2026-06-15 survey surfaced that **no native SKILL.md exists for consumer shopping price
comparison**, every "skill bundle" in the wider ecosystem (coreyhaines31/marketingskills 32.6k★,
alirezarezvani/claude-skills 338-skill bundle, ComposioHQ/awesome-claude-skills 63.8k★) targets
marketing / SEO / seller-side intel. Consumer price compare was a gap. This skill fills it as a
sister to market-intel, market-intel handles broad commercial research, shopping-aggregator
handles the consumer buy decision.

### Initial content

**9 domain shards:**
- amazon-us
- ebay-walmart-target
- taobao-tmall
- jd-pdd
- browser-extensions (incl. ⚠ Honey 2026 status: avoid)
- mobile-apps-aggregators
- ai-shopping-assistants
- claude-mcps
- oss-self-host

**17 tool docs** (per-tool how-to: install + auth + usage + gotchas):
- Amazon history: keepa, camelcamelcamel
- Multi-platform MCPs: biggo-mcp, apify-price-intelligence, taobao-mcp, oxylabs
- US retailer API: ebay-api
- CN tools: manmanbuy, gwdang, smzdm
- US browser extensions: capital-one-shopping, karma-extension, coupert, ⚠ honey
- US deal/aggregator apps: slickdeals, shopsavvy, flipp
- AI shopping: perplexity-shopping
- OSS self-host: pricebuddy, priceghost, pricedive, discount-bandit

**Support docs:**
- `SKILL.md`, orchestration core with 7-step workflow (parse intent → triage → detect → install
  guide → delegate → normalize landed cost → record live-run)
- `sources-index.md`, thin domain index
- `install-guide.md`, L0 install mechanics + secret hygiene + Windows notes
- `report-template.md`, landed-cost ranking + history note + risks + gaps template
- `refresh-protocol.md`, monthly cadence; weekly for browser-extensions + AI assistants
- `volatile/pricing-install.md`, per-domain install commands + prices, time-stamped
- `tools/index.md` + `tools/registry.json`, three-way consistency-checkable tool catalog

### Shopping-specific guardrails (in addition to market-intel's general ones)

1. Snapshot timestamp is mandatory on every price entry.
2. Stock state is part of the price.
3. Landed cost (ship + tax + coupon - cashback), not sticker.
4. Coupon verification via playwright cart test, not extension badge.
5. Retailer trust tiers L1 first-party → L5 unverifiable.
6. No silent degradation when a primary source is missing.
7. Cross-snapshot disagreement → re-fetch, don't average (Buy Box rotation).
8. Disconfirmation mandate (counterfeit / DOA / fraud reverse-search).
9. Failures become explicit gaps.
10. Affiliate disclosure tracking, extension "savings" don't bias the ranking.

### Notable inclusions

- **Honey 2026 status proactively surfaced**, MDL active discovery (Jun 2026), Rakuten/Impact/Awin
  affiliate-network terminations (Jan 2026), recommendation: uninstall.
- **Amazon PA-API 5.0 marked dead** (✗ retired 2026-05-15, replaced by Creators API).
- **PriceDive** (53★, Python) called out as the **only fresh OSS for CN multi-platform**
  (Taobao/JD/PDD), non-obvious without the survey.
- **pricebuddy** (962★) + **PriceGhost** (641★) called out as the modern OSS picks for Western
  markets, **above** older Discount-Bandit recommendation in market-intel's
  ecommerce-arbitrage shard.

### Cross-skill integration

- `DaizeDong/market-intel` ready-skills shard adds a row pointing here.
- market-intel sources-index adds a `consumer-price-compare` domain row pointing to this repo.
- A new market-intel `domains/consumer-price-compare.md` shard documents the boundary.

### Known limitations of v0.1.0

- No anti-regression CI gate yet (heartbeat only). Planned v0.2, port market-intel's
  `verify_matrix.py`.
- No CONSTITUTION.md hard-constraint injection yet.
- 17 tool docs (vs market-intel's ~150), minimum viable, expansion in v0.2.
- No per-state US sales tax tables yet (NJ assumed in default examples).

See [ROADMAP.md](ROADMAP.md) for v0.2 plan.
