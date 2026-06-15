# Tool: Perplexity Shopping

- **Domain(s):** ai-shopping-assistants
- **Barrier route:** ① · **Source tier:** L2 (LLM-aggregated) · **Ready MCP:** no (chat interface)
- **Cost:** free tier; **Pro $20/mo** for in-app PayPal checkout
- **Repo / Provider:** perplexity.ai/shopping — Perplexity AI
- **Top pick for its domain:** yes (only conversational AI shopping with live checkout)

## What it does / when to pick it
Conversational AI shopping assistant. Ask in natural language ("quiet ANC headphone under $300, comfortable for long flights") → returns compared products with prices, reviews summary, retailer links, and (for Pro users in US) one-click PayPal checkout across 5000+ merchants (Nov 2025 launch). Pick as a **sanity-check fallback** or for vague-intent discovery — NOT as the primary price oracle (LLM hallucinates ~5-10% of specific claims).

## Install
**User-side**: perplexity.ai → sign up. Free tier covers basic shopping queries; Pro for in-app checkout + higher rate limits.
**Skill-side**: there's no MCP integration; this is consulted manually or via the user delegating "ask Perplexity for me."

## Auth / keys
User account for Perplexity. Pro is paid ($20/mo).

## Usage — call examples
N/A for the skill directly. If the skill *does* want to compare its own recommendation to Perplexity's, the user opens perplexity.ai and pastes the buy intent — then reports back. Or use the user's Perplexity account via the existing perplexity browser if it's logged in (playwright).

## General experience & gotchas (踩坑)
- **Hallucination rate** ~5-10% on specific product claims and reviews — independent audits 2025-2026 documented this. Always cross-check prices against the actual retailer page; treat review summaries as ⚠ unverified-by-default.
- **Affiliate / commission bias** — Perplexity monetizes via PayPal merchant commissions. The "recommended" product may be partly biased by commission rate. Mitigation: ask for **3 alternatives**, not 1, and independently rank.
- **US-only checkout** — international users can browse but not checkout in-app.
- **Strength**: discovery for vague intent ("quiet headphones for the gym"); review summarization (with caveats).
- **Weakness**: real-time pricing accuracy; deal/coupon discovery; cross-regional compare.

## Failure signals & fallback
Hallucinated product not on the linked retailer; price off by >$20 vs actual retailer page. **Fallback:** the skill's own playwright/BigGo/Keepa pipeline; treat Perplexity as a sanity-check input, not source of truth.

## Last verified: 2026-06
