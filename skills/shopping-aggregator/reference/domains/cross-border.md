# Domain: cross-border

**Triage signals:** 海淘、代购、daigou、parallel import、grey market、"ship to US from China/Korea",
package forwarder / 转运, Superbuy, MyUS, Stackry, YesStyle, Stylevana, Olive Young, StyleKorean,
AliExpress direct, "is the warranty valid if I import it", "customs / duty / tariff on my order".

> **This is a CROSS-CUTTING shard, not an access-method one.** The supply-side shards
> (`amazon-us`, `taobao-tmall`, `jd-pdd`, …) read prices *within one market*. This shard owns the
> **landed-cost-across-a-border** layer that sits on top of them: duty, the forwarder/daigou markup,
> and the warranty/authenticity penalty of buying outside the authorized in-region channel. It maps to
> the **cross-border / import** channel class in [`channel-classes.md`](../channel-classes.md) — that
> class enumerates *which* importers; this shard is *how to price and risk-rate* the import.

## IRON LAW for this shard (de-minimis is the single most decision-changing, most volatile fact)

**Do NOT restate any de-minimis threshold, duty rate, or per-item flat fee inline here.** The single
source-of-record for those numbers is [`../data/cross-border-duty.json`](../data/cross-border-duty.json)
(see [`../data/README.md`](../data/README.md) "Volatility note"). Read the JSON at runtime, cite its
`source_url` (CBP / Federal Register / White House primary pages) and `verified_date`, and never quote a
number from this prose or from memory. This shard describes the *shape* of the rule and the *channels*;
the JSON holds the *figures*.

What the prose IS allowed to say (structure, not figures): **as of this shard's `Last verified`, US
duty-free de-minimis is no longer a usable assumption** — it was suspended for China/HK first, then for
**all countries**, and is on a statutory path to permanent repeal. Treat *every* cross-border consumer
parcel as **dutiable** until the JSON says otherwise for that origin. The old "under the threshold → free"
mental model is dead; pricing must add duty by default. (Origin-specific dates, the all-country effective
date, the flat per-item postal fee, and the repeal date all live in the JSON rows, each E1-graded with its
primary `source_url`.)

## Source matrix (the cross-border *channels*)

| source | route | capability | detect | risk / trust tier |
|---|---|---|---|---|
| **Package forwarder — Superbuy** ([superbuy.com](https://www.superbuy.com/en/page/guide/feecomposition/)) | ④ buyer-op | CN→US: buys on Taobao/Tmall/JD/1688 for you, warehouses, consolidates, reships. **No purchasing service fee on those 4 platforms** (fee only on 2nd-hand/unlisted); 90-day free storage. Adds: int'l shipping + add-ons (photos/repack). | superbuy.com account | mid; you still pay full CN duty on entry; shipping on the higher side per comparisons |
| **Package forwarder — MyUS** ([myus.com/pricing](https://www.myus.com/pricing/)) | ④ buyer-op | Generic US-address reship (US store → you abroad, or used in reverse for US-warehoused goods). **FL warehouse → 0 US sales tax**; Premium tier ($9.99/mo or $60/yr) = free consolidation + 30-day storage; weight-based TruePrice. | myus.com account | low-mid; subscription model; many newer rivals are no-fee |
| **Package forwarder — Stackry** ([stackry.com/pricing](https://www.stackry.com/pricing)) | ④ buyer-op | US-address reship. **Free membership, no monthly fee**; **NH warehouse → 0 US sales tax**; ~per-package consolidation fee (small, capped); 45-day free storage; low add-on fees. | stackry.com account | low; cheapest-tier pick, but rates climb on bulky parcels |
| **Daigou / 代购** (individual buyers, WeChat/Xiaohongshu) | ④ human | Person in-region buys at local/member/event price and reships. Can reach in-app-only prices (88VIP, 직영 KR exclusives) a forwarder's warehouse cannot. | personal network / agent shop | **HIGH**: opaque markup, authenticity unverifiable, no recourse; trust tier L4-L5 — never the ranked winner |
| **AliExpress (direct / Choice / Cainiao)** ([aliexpress.com](https://www.aliexpress.com/)) | ④ / ① platform | CN seller → US direct. Duty model is **DDP (prepaid at checkout, "tax included")** for eligible orders vs **DDU (carrier bills you on delivery + handling fee)** for others. **"Ship from US" filter = domestically warehoused, no import duty** and faster — prefer it. | aliexpress.com | mid; carrier handling fee can exceed the duty on small orders; seller trust varies |
| **Asian-beauty cross-border retailers** (YesStyle / Stylevana / Olive Young Global / StyleKorean) | ④ / ① | KR/JP/CN beauty → US. **YesStyle**: tariffs folded into price, reimburses any duty bill as credit. **Olive Young Global / StyleKorean**: duty added post-de-minimis; some KR-formula SKUs now restricted to US. **Stylevana**: lowest free-ship threshold of the group. | the retailer's site | mid; mixed CS / refund / authenticity reports — treat as L3, verify per-SKU |

**Default pick:** **CN→US bulk/long-tail Taobao haul → Superbuy** (no service fee on the big 4 platforms +
consolidation). **US-address generic reship → Stackry** (no membership, tax-free NH) unless the user ships
often enough that **MyUS Premium** consolidation pays back. **K/J-beauty → YesStyle** (it absorbs the tariff)
over Olive Young Global for US buyers right now. **Daigou only when a price is structurally unreachable any
other way, and never as a ranked winner** (trust tier too low).

## Real-run lesson

1. **The de-minimis era is over — re-pricing, not a footnote.** Pre-2025 cross-border math assumed "small
   parcel = duty-free." That assumption is dead (all-country suspension; statutory repeal pending). Every
   cross-border quote MUST add duty from [`../data/cross-border-duty.json`](../data/cross-border-duty.json)
   by default; a quote that shows only item + shipping is **wrong**, not merely optimistic.
2. **Forwarder markup is multi-line, not one fee.** Landed = item + CN-domestic ship + (service fee, often 0
   on Superbuy's big-4) + consolidation + int'l ship + **duty on entry** + (carrier handling fee if DDU) +
   add-ons. Quote the *stack*, timestamp it, and name the warehouse state for the sales-tax line (FL/NH = 0).
3. **Carrier handling fee is a hidden tax on cheap parcels.** On a small order the fee to *collect* the duty
   can dwarf the duty. DDP (prepaid at checkout) usually beats DDU (pay-on-delivery) for small US orders —
   flag it.
4. **Grey-market / parallel-import = genuine goods, but warranty generally void.** Products are authentic
   (first-sale doctrine), but manufacturers typically **refuse warranty service outside the authorized
   in-region channel**, sometimes using region-specific model numbers to detect imports. For any
   warranty-sensitive category (electronics, watches, appliances) the report MUST state: "imported via
   `<channel>` → manufacturer's US warranty likely **not honored**; only the seller's own (if any) applies."
   This belongs in the risks section, not buried.
5. **Daigou prices are unverifiable by construction.** A daigou screenshot is not an E1 read — there is no
   PDP to re-fetch, no authenticity proof, no recourse. Cap it at trust tier L4-L5; surface it as context,
   never rank it #1.
6. **Beauty cross-border thresholds & tariff handling churn fast.** Free-ship thresholds and "does this site
   absorb the tariff" change month to month. Treat the prose figures here as **direction, not gospel**; the
   *only* numbers a report should commit to are a live read of the retailer's cart + the JSON's duty rows.

## Channel cross-links

- **Which importers exist for a product** → [`../channel-classes.md`](../channel-classes.md), row
  **cross-border / import**. That file is the demand-side enumerator; this shard is the pricing+risk layer.
- **The market being imported FROM** → the supply-side shard for that market reads the in-region price first
  (e.g. [`taobao-tmall.md`](./taobao-tmall.md), [`jd-pdd.md`](./jd-pdd.md), [`amazon-us.md`](./amazon-us.md)),
  then THIS shard adds the border layer on top. `taobao-tmall.md`'s "跨境（海淘/代购）说明" and `jd-pdd.md`'s
  京东国际 note both hand off here.
- **The numbers** → [`../data/cross-border-duty.json`](../data/cross-border-duty.json) (de-minimis, duty,
  flat fees) — the single source-of-record, CBP-primary. Never inline them.

**Install guidance:** no install — all channels are buyer-operated accounts + ④ playwright for live reads.
Forwarder/retailer accounts are created by the user (login/payment hand-off); the agent prices via playwright
on the live cart and the duty JSON.

## Last verified: 2026-06
