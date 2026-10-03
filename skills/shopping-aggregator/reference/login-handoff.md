# Login handoff, the third access state

> **WHY this file exists.** The rest of the matrix models a source as two-state: **anonymously
> readable**, or **unavailable**. Real consumer marketplaces have a third state, and it is the one
> the operator cares most about: **session-gated**, readable in full the moment a human logs in
> once, and returning nothing at all until then. With no vocabulary for that state, the skill did
> the only thing it could and filed the channel as a `coverage_gap`, while the person who wanted
> the answer was sitting right there and could have unlocked it in ten seconds. That is not a
> coverage limit. It is **a handoff that was never designed.** This file designs it.
>
> Read it at **Step 3** (access-state detection) and whenever a route returns empty behind a login
> prompt. `last_verified: 2026-07`

## The three access states (replaces the available / unavailable binary)

| state | meaning | what the skill does |
|---|---|---|
| **S1 anonymous** | a real read lands with no session | fetch it, grade normally (`E1` if PDP/API) |
| **S2 session-gated** | the page loads, but content requires a logged-in session; the operator plausibly has or can make an account | **HANDOFF (below).** Never a `coverage_gap` until the operator has been asked and has declined or is absent |
| **S3 structural** | no session the operator can supply would help: geo-block, dead domain, closed API, region-locked, commercial proxy pool required | genuine `coverage_gap`, declare up front, do not burn retries |

**Classifying S2 vs S3 is the whole job.** Getting it wrong in the S3 direction silently throws away
a reachable channel; getting it wrong in the S1 direction produces the empty-result trap below.

## The empty-result trap (this is why S2 must be detected, not inferred)

A session-gated marketplace search does **not** error. It renders its own shell, its filters, even a
recommendation carousel, and reports **"no results found"**. That is byte-for-byte the same shape as
"nobody is selling this," and it will be read as a price finding unless you force it not to be.

**HARD RULE, the control query.** Before recording *any* zero-result from a marketplace search, run
a second query for a term that platform certainly has thousands of live listings for (the bare
category noun, the platform's own homepage-featured term). If the control **also** returns zero, the
search layer is not working for you and **every zero from that platform this run is void**: it is an
S2/S3 signal, never a stock signal. Record the control query and its result alongside the finding.

Corollary: cookies are not the test either. Loading the homepage first to collect a full set of
risk-control cookies, then re-querying, has been observed to change nothing. Do not spend a second
round on it; a control query settles it in one call.

## The handoff protocol

Applies when an **in-scope** channel class resolves to S2 and the operator is present in the session.

1. **Finish everything else first.** Do all S1 work, all landed-cost math, all verification. The
   handoff is the last blocking step, not the first, so a declined handoff still ships a full report.
2. **Batch the asks.** Collect every S2 channel into **one** request. Asking N times, once per
   platform, is the failure mode this protocol exists to avoid; the operator should log into all of
   them in a single sitting.
3. **Take exclusive control of the browser.** See "Concurrency" below. Never attempt a handoff from
   inside a parallel subagent.
4. **Open the login page and STOP.** Navigate to the platform's own login URL. Do not click, do not
   type, do not submit, do not touch a credential field or a QR code. **Emit no further tool calls
   against that browser.**
5. **Hand off explicitly**, naming: which platform, why it is needed (which coverage gap it closes),
   what exactly will be read afterwards, and the **resume signal** (a plain "logged in, go ahead").
   Then **end the turn.** Waiting means ending the turn, not polling in a loop.
6. **On resume, verify the session before using it.** Re-run the *control query* from above. A
   control that now returns results confirms the session is live; a control that still returns zero
   means the login did not take (wrong account, marketplace-ineligible account, region block) and
   the channel is S3 after all. Say which.
7. **Export and absorb before reading.** Unconditionally export the complete context, including
   IndexedDB, to private staging; run the installed session-store absorber and check success.
   Then perform the scoped reads. Follow the persistence procedure below.

## Hard rules

- **The agent never authenticates.** It does not type usernames, passwords, SMS codes, TOTP codes,
  or scan QR codes; it does not create accounts; it does not use saved credentials it happens to
  find. The human logs in. The agent resumes afterwards. No exception, not even if the operator
  pastes a password into the transcript (if they do: tell them not to, and ask them to type it into
  the browser instead).
- **A logged-in page is a PII surface.** After resume, `browser_snapshot` / screenshots MUST be
  scoped to the product content. Never snapshot account, order-history, address-book, saved-payment,
  or messaging views; those render the operator's real name, addresses, and order history into the
  transcript. This extends CONSTITUTION V.3 from API keys to session PII.
- **Read-only after resume.** An authenticated session makes destructive and financial actions
  reachable that were impossible before. Post-login the agent may navigate and read. It MUST NOT
  place an order, bid, make an offer, message a seller, save an address, or change any setting
  without a fresh, explicit, per-action instruction. Adding to a cart to reveal a tax line is
  permitted only with restoration: record the existing items and quantities first, remove only
  what the probe added, and re-read to confirm the original cart is restored. Prefer a disposable
  cart or session; preserve every unrelated item.
- **Never a substitute for the operator's judgement about which platforms to touch.** If the
  operator has said a platform is off-limits for automated logged-in use, that stands; do not
  propose a handoff for it.

## Browser ownership during a handoff

Assign one workflow to the context used for the login handoff. Pause other work in
that context until login, control query, export and absorption finish. Confirm
actual context/profile isolation before allowing other browser workers to proceed;
a shared MCP connection can still share tabs. Address pages by their own handles.

## Session persistence, EXPORT IS MANDATORY, not optional

A browser launched with an isolated/ephemeral profile discards everything on exit, and a
`--storage-state`-style seed file is a **READ-ONLY input**: nothing writes back on its own. So an
operator login that is not exported is **destroyed when the browser closes**, and the next run
re-interrupts them for the same login. That is the single most wasteful outcome of this protocol.

**Therefore: immediately after the resume control query passes, export the session state.** Before
reading prices, not after: the read can fail, the export must not be what you lose.

- Export the entire context with `context.storageState({ path: incomingPath, indexedDB: true })`.
  Do this unconditionally after the control query succeeds and before scoped reads. Include all
  cookies, origins and IndexedDB state; do not filter to the site just used or try to infer whether
  a new login occurred. If the installed browser cannot export IndexedDB, repair that capability
  before claiming persistence succeeded.
- `incomingPath` must be a unique file in the operator's configured private incoming directory.
  Never write directly over the shared seed. Run the installed `pw-auth.py absorb` helper after
  export and verify its exit status. The absorber merges the full context into the per-site stores
  and rebuilds the union seed. Check domains and counts only; an unabsorbed file is still pending.
- Keep staging, site stores and the union seed outside every public worktree. Retain the durable
  stores in the operator's authorized, verified PRIVATE versioned configuration backup. A missing
  private destination or failed absorption is a persistence failure, not permission to write into
  this skill repository. Cookies and IndexedDB may contain bearer credentials.
- **Never print cookie values.** Report domains and counts only (CONSTITUTION V.4).
- Treat an existing session file as a **capability, not a fact**: it may be stale. Validate with the
  control query before trusting a read, same as a fresh login. Expiry metadata is a poor proxy,
  anti-bot token cookies rotate in minutes and will make a perfectly good store look expired.

### QR codes expire while you wait

A handoff that offers a QR login has a clock on it. Observed: the operator returned, and the code
had already lapsed to "expired", so the handoff appeared to have failed when nothing was wrong.

- **Refresh the login widget immediately before handing off**, so the operator gets a full validity
  window rather than the tail of one.
- If the operator reports back and the control query still fails, **re-check for an expired code
  before concluding the channel is S3**. Reload, hand off again, and say why.
- Prefer navigating to the target search URL (not a bare login page) when you refresh, so that the
  moment the login lands the page is already showing what you need to read.

### Sites that refuse to be logged into by an automated browser

A minority of providers detect the automation surface and block **sign-in specifically**, while
still honouring a session cookie created elsewhere. The symptom is a login that fails only inside
the automated browser, typically with a "this browser may not be secure"-shaped message. For that
class the handoff as written cannot succeed, and the fix is to seed the store from a login
performed in the operator's **ordinary** browser instead. Classify the site as S2 still (a session
does solve it) and note that the login must happen out-of-band.

**Do not predict which sites these are, and do not pre-emptively route around them.** This
reputation is stale far more often than it is accurate: providers widely believed to block
automated sign-in have been observed completing a normal interactive login inside a current
Playwright browser with no special flags. Announcing "this one will be blocked" before trying it
wastes the operator's time and can talk them into a heavier workaround they never needed. **Offer
the ordinary handoff first; treat out-of-band seeding as the fallback you reach for after an actual
observed block, never as the opening move.**

## When the handoff is declined or the operator is absent

Both are normal outcomes, and neither is a failure of the run.

- Record the channel with `outcome: coverage_gap` and **`gap_reason: session-gated-declined`** (or
  `gap_reason: session-gated-unattended` for a headless / scheduled run), which is a *different* fact from
  `structurally-unreachable`. The taxonomy matters: the first says "one login away," the second says
  "no login helps." Preserve the same `gap_reason` in the report and private live-run record; put
  supporting observations in `detail`. A future run should retry the first and not waste effort on the second.
- **Do not substitute another channel's numbers for the missing one.** If the operator asked for a
  specific marketplace's going rate, a different marketplace's prices do not answer that question.
  Say the cell is empty.
- Report what the handoff *would have* bought, in one line, so the operator can decide whether to
  come back and unlock it.

## Observed platform notes

Facts about platforms, not about any product or shopper.

- **CN social/C2C marketplaces** (the goofish/dewu/zhuanzhuan/weidian class) are **S2 for search
  itself**, not merely for checkout: the anonymous SERP renders shell plus filters plus a
  recommendation carousel and reports zero results for everything, including the bare category noun.
  Additionally, **no search engine indexes their product pages**, so the usual "find it via SERP,
  then open the direct URL" bypass does not exist for this class. Engine-based bypasses work for
  *content* sites (video, blog, wiki, deal-aggregator) and systematically fail for CN commerce PDPs.
- **CN mainstream commerce** (the taobao/tmall/jd class) has extended the wall from search to the
  **PDP itself**; holding a SKU id no longer implies you can read its price. Their price
  micro-APIs are also unreliable from outside the region (internal-IP DNS answers, dead endpoints).
- **Some price-history sites inherit the wall**: they require their own social login before showing
  a curve for a gated retailer, so they are S2 too rather than a bypass around it.
- **Daigou / forwarding agents are not a read bypass.** Their product search and their
  paste-a-URL rendering both sit behind the same login, and their supported-platform list may
  exclude a retailer outright. What is often anonymous on those sites is the **freight calculator**,
  which is worth reading on its own for landed cost.
- **A major auction platform's sold-comps view is S2 now** where it was long S1. Treat "sold comps
  are free and open" as an expired fact and check, do not assume.
