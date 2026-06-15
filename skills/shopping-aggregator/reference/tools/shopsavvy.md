# Tool: ShopSavvy

- **Domain(s):** mobile-apps-aggregators
- **Barrier route:** ① mobile app · **Source tier:** L2 · **Ready MCP:** no
- **Cost:** free
- **Repo / Provider:** shopsavvy.com — iOS + Android
- **Top pick for its domain:** yes for **in-store barcode-scan price compare**

## What it does / when to pick it
Mobile app that scans a barcode (UPC/EAN) in a physical store and shows online + competing retailer prices. Pick when the user is **physically in a store** (Costco, Target, Best Buy) and wants to know "is this cheaper online or at <competitor>". Useless for online-only sessions — playwright / BigGo wins.

## Install
App Store / Google Play search "ShopSavvy". v18.9.40+ Jun 2026.

## Auth / keys
Free, optional account for watchlist / sync.

## Usage — call examples
**user-side only** — agent cannot scan barcodes from your text channel. If user describes "I'm at Costco looking at a Sony X95L, the SKU is XBR-65X95L" → ShopSavvy can't help via agent; the *user* opens the app and scans.

The skill should **recommend ShopSavvy when the buy intent has a "currently in physical store" flag**.

## General experience & gotchas (踩坑)
- **Coverage on lightly-trafficked physical SKUs** can be sparse — long-tail electronics work better than long-tail apparel.
- **Retailer list is opaque** — the app claims 100k+ retailers but doesn't expose which queue per scan.
- **Camera scan quality varies** — low light / glare = fail; manual barcode entry as fallback.
- **In-store-only deals** (Costco member-exclusive, Sam's Club Plus prices) won't show — these aren't online-indexable. Acknowledge gap.
- **Doesn't replace the loyalty-program scan** — e.g. Target Circle in-store deals require Target app.

## Failure signals & fallback
Barcode not recognized; no prices returned. **Fallback:** Google Lens (more flexible scanner, no in-store-deal lens) or Google Shopping (manual SKU search).

## Last verified: 2026-06
