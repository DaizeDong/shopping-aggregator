# Domain: ai-shopping-assistants

**Triage signals:** "use AI to shop", "Perplexity Shopping", "ChatGPT find me the cheapest",
Rufus, Alexa shopping, Klarna AI, Daydream.

| tool | status (2026-06) | strength | gotcha |
|---|---|---|---|
| **Perplexity Shopping** ([perplexity-shopping.md](../tools/perplexity-shopping.md)) | ✓ live, expanding | conversational price/compare/reviews; 5000+ merchants via PayPal in-app checkout (Nov 2025) | **US-only checkout**; in-app buy requires Pro $20/mo; reviews can be hallucinated, verify against source |
| **ChatGPT Shopping** | ⚠ rolled back to discovery-only Mar 2026 | conversational product discovery, links to retailers | Instant Checkout (Sept 2025) **was reversed Mar 2026**, now ChatGPT shows products but checkout is back to the merchant; OpenAI tightened guardrails after merchant disputes |
| **Amazon Rufus** | ✗ sunset 2026-05-13 | (was) in-PDP AI Q&A on Amazon | folded into **Alexa+ Shopping Agent** (replacement); functionality preserved but UX different |
| **Alexa+ Shopping Agent** | ✓ live (replaces Rufus) | Amazon-only catalog Q&A + voice shopping | Amazon-only, Echo / Alexa app entry points |
| **Klarna AI assistant** | ⚠ partial rollback to hybrid (CEO walked back AI-only cuts) | BNPL + AI Q&A on Klarna's merchant network | routine queries only; complex returns / disputes back to human reps |
| **Daydream** | ✓ $15M A Apr 2026; 2000+ fashion brands | **fashion only**, conversational discovery | very narrow category; not for electronics/home |
| **Bing Copilot Shopping** | ⚠ low-priority; integrated with Bing search | basic price compare in SERP | weaker than Perplexity; Microsoft has not heavily pushed this lane |

**Default pick:** **Perplexity Shopping (Pro $20/mo)** is the only conversational AI shopping
assistant with end-to-end (search → compare → checkout) flow that's both live and US-supported.
For Amazon-specific: Alexa+ (Rufus successor). For fashion: Daydream.

## How they fit this skill

These AI assistants are **competition** more than allies, they do user-facing what
shopping-aggregator does for the agent. But they're useful as:
1. **Sanity check fallback**: ask Perplexity the same question, compare its recommendation to ours
, if both converge, higher confidence; if diverge, investigate.
2. **Review/reputation lookup**: Perplexity is good at summarizing review consensus (caveat: it
   hallucinates ~5-10% of review claims, verify).
3. **Discovery for vague intent**: "I want a quiet ANC headphone under $300", Perplexity can
   narrow the field; shopping-aggregator then compares specific picks.

## Hallucination guardrail (mandatory)

LLM shopping assistants invent product specs, prices, and reviews regularly. When using
Perplexity/ChatGPT as an input source:
- **Cross-check every price** against the actual retailer page (playwright).
- **Cross-check every spec claim** (battery life, dimensions) against the official product page.
- **Treat review summaries as ⚠ unverified-by-default.** Pull at least 3 verbatim reviews from
  the retailer page to corroborate.

These models had product/price hallucination caught at ~15% rate in informal 2025-2026 audits;
ChatGPT's checkout rollback (Mar 2026) was partly driven by merchant complaints about
wrong-product / wrong-price recommendations.

## What's NOT in this domain

- **Shop-mode chatbots on retailer sites** (Walmart "Sparky", Best Buy bot), single-retailer
  customer service tools, not price-compare. Skip.
- **Generative search at Google**, "AI Overviews" sometimes includes shopping; treat as
  Bing Copilot tier (weaker).
- **TikTok Shop AI assistants**, pure marketing layer over TikTok Shop catalog, not cross-store.

## Affiliate / commission model

Perplexity Shopping monetizes via PayPal merchant commissions. ChatGPT was doing the same before
the Mar 2026 rollback. This means: the "recommended" product is sometimes biased by which
merchant pays Perplexity highest commission. Mitigation: ask Perplexity for **3 alternatives**
not 1, then independently rank.

**Install guidance:** these are SaaS apps; open the URLs in tool docs. No MCP install.

## Last verified: 2026-06
