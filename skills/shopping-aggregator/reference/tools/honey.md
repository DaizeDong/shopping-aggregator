# Tool: ⚠ PayPal Honey — AVOID (status 2026-06)

- **Domain(s):** browser-extensions
- **Barrier route:** ① free service · **Source tier:** L3 → effectively L5 (catalog gutted) · **Ready MCP:** no
- **Cost:** free
- **Repo / Provider:** joinhoney.com — PayPal-owned since 2020
- **Top pick for its domain:** **NO — uninstall recommended**

## ⚠ Status

**Active legal action + affiliate network terminations as of 2026-06.** Document, do not install:

- **MDL "In Re PayPal Honey Browser Extension Litigation"** consolidated and in **active discovery as of Jun 2026** (cohenmilstein.com case page).
- **Arbitration motion DENIED Nov 2025** — case proceeds in US federal court.
- **Rakuten terminated Honey from its 2000+ merchant affiliate network on 2026-01-12** (ppc.land report). **Impact.com and Awin followed within weeks.**
- No product-behavior changes announced by PayPal. The product still loads but its actual coupon coverage has been gutted.
- Most personal-finance press and creators in 2026 recommend uninstalling.

## Why include a doc for an avoid-tool

Users may still have Honey installed (it was the default for years). The skill should **detect** when the user mentions Honey and proactively recommend uninstalling + a healthy replacement (Capital One Shopping / Karma). Source of accusations (paraphrased):

1. **Last-click affiliate hijacking** — replaces creator/blogger referral cookies with Honey's at checkout.
2. **Suppressed coupons** — allegedly hid better codes than the one shown, in exchange for merchant payment.

These are MegaLag's 2024 video allegations that became the lawsuit basis; PayPal disputes them in court.

## Install
**Do not.** If user has it installed: Chrome → Extensions → Honey → Remove.

## Auth / keys
N/A.

## Usage — call examples
N/A. **The skill should never positively recommend this tool.** If the user explicitly asks about it, surface the status above and the replacement set (`reference/domains/browser-extensions.md`).

## General experience & gotchas (踩坑)
- **Honey app on iOS/Android** is still on the stores; same caveat applies — the catalog backing it has shrunk.
- **PayPal Rewards / Honey Gold** balances may still pay out; user should redeem any remaining balance before uninstalling.
- **Coverage shrinkage is silent** — the extension UI still shows "100+ coupons available" while the working code count has dropped. Don't trust the badge.

## Failure signals & fallback
Use **Capital One Shopping** + **Karma** (or **Coupert**) — see `reference/domains/browser-extensions.md`.

## Last verified: 2026-06
