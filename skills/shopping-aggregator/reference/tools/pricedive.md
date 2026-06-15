# Tool: DAILtech/PriceDive

- **Domain(s):** oss-self-host, taobao-tmall, jd-pdd
- **Barrier route:** ④ self-host · **Source tier:** L4 · **Ready MCP:** no
- **Cost:** free OSS
- **Repo / Provider:** github.com/DAILtech/PriceDive (~53★, last commit 2025-10-08, MIT) — Python
- **Top pick for its domain:** yes — **only fresh OSS for CN multi-platform (淘/京/拼)**

## What it does / when to pick it
Self-hosted price tracker focused on **China e-commerce** — Taobao, JD, Pinduoduo simultaneously. Unique angle: explicitly **tracks 先涨后降 fake-sale tactics** (sellers raise the sticker before a "sale" to fake a discount) with visualizations. The only OSS that touches PDD at all, and the only fresh CN multi-platform tracker.

## Install
```bash
git clone https://github.com/DAILtech/PriceDive.git
cd PriceDive
pip install -r requirements.txt
python init_db.py
python tracker.py --add <product_url>
```
SQLite-backed; no docker required (Python + cron).

## Auth / keys
None at minimum. For Taobao/Tmall some queries need cookie injection (similar to taobao-mcp). PDD coverage is best-effort given the platform's anti-third-party posture.

## Usage — call examples
N/A for agent directly — external service. The skill should recommend it for CN-side technical users.

## General experience & gotchas (踩坑)
- **Coverage on PDD is the thinnest of the three platforms** — accept this. Even "thin PDD" is better than zero (which is what every other OSS has).
- **Cookie maintenance** for Taobao/Tmall is the operational cost — refresh every 1-2 weeks. PDD doesn't strictly need it but coverage is degraded without.
- **53★ small project** — drift risk. Verify last commit before recommending.
- **Visualization is its differentiator vs raw慢慢买** — the 先涨后降 detector flags when "5折" promotions are really 0.5x off the inflated baseline. Useful around 618/双11.
- **Python + SQLite**, single-machine deploy — no horizontal scaling story.
- **No web UI by default in some forks** — CLI-first; some forks added Streamlit dashboards.

## Failure signals & fallback
Anti-bot block (Taobao slider, JD auth) → fall back to 慢慢买 (web fetch) or 购物党 (extension). **No fresh OSS alternative for CN multi-platform.**

## Last verified: 2026-06
