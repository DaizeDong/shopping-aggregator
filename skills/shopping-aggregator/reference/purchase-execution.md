# Purchase execution (retail orders; read only when the buyer has instructed a purchase)

The rest of this skill decides where and at what price to buy. This file covers the step after that decision, when the buyer says "buy it" and means it. It applies to **retail product orders only**: lodging and flights stay hand-off-only per [lodging](domains/hotel-travel.md) and [air travel](domains/air-travel.md), which stop at the confirmation page.

`last_verified: 2026-10`

## The invariant

**Execute the #16 stack, not the sticker.** The default is the purchase path whose own stack totals lowest at checkout, with every eligible discount stacked. A one-time path can carry its own coupon or deal price, so "subscription" is not automatically the answer; the lower charged total is. Plain one-time is correct only when nothing applies or the buyer declined the commitment, and the report must have said which.

If no report in the session covered this offer (the buyer pasted a link or named a retailer), or the report headlined a sticker without saying why, build that offer's #16 stack first ([SKILL.md](../SKILL.md) Step 6, cart-tested), then buy that.

## What may be bought on announcement, and what needs a yes

- **A subscription that is cancellable without fee** may be bought on announcement: say which option you are buying and why it is cheaper, then buy it. Count it as fee-free only after reading its terms: no minimum number of deliveries, no fee or clawback for cancelling after the first, and whether the discount covers later deliveries. Use the interval the buyer named, otherwise the profile's `purchase_defaults.subscription_interval` (`page-default`, or no profile, means the page's own), and report the next delivery and charge date and how to cancel. A profile whose `purchase_defaults.subscriptions` is `ask` turns this announcement into a question; `decline` keeps subscriptions out of the stack ([CONFIG.md](../../../CONFIG.md)).
- **Anything else that changes what the buyer approved needs an explicit yes before any submit**: a minimum quantity or a multi-pack, a prepaid plan, a non-cancellable term, a slower delivery that misses the buyer's deadline, or a change of fulfillment such as pickup instead of shipping.
- **A discount that needs the buyer to join or sign up** (a membership or free trial, an email or SMS list, a new account, a store card, a portal account) is the buyer's decision: name it with its cost and ask. Never start a trial, application or sign-up, and never type the buyer's email or phone into a form.

## Boundaries that do not move

- **A fresh, explicit, per-action instruction is required** (CONSTITUTION V.4). It covers this item, this quantity and this order. It does not cover another item, a different quantity, or a second order: after any failed or stalled submit, confirm in order history that nothing was placed before trying again under the same instruction.
- **The agent never authenticates and never enters payment details.** If checkout needs a login, a code or a card number, hand off to the buyer (see [login handoff](login-handoff.md)).
- **The profile says who may submit at each retailer.** Its `accounts[]` entry for the retailer's exact host must say `checkout: agent` before the agent clicks. `owner-browser`, a missing entry, or a run without a conforming profile moves the final click to the buyer (below); the agent still prepares the stack. `none` means no order through that account at all: say so and stop.
- **Read logged-in pages by scoped text extraction of named fields** (item, quantity, discount lines, totals, order number, delivery promise, payment type). Never take a snapshot or screenshot of a checkout, order, account, address or payment page. Check the destination by comparing it in-page with the Step 1 ship-to ZIP (the profile's `ship_to.zip` unless the buyer named another destination) and output only match or mismatch.

## The procedure

1. **Baseline and re-read.** Record the cart's items and quantities, or use a path that bypasses the cart. Re-read the offer live: price, seller, stock and each purchase path's price. If the re-read changes which path is lowest, take the lowest (asking only if it adds a commitment) and say so; a lower total is fine, a higher one means stop and report.
2. **Activate before adding to cart.** Do every activation the stack needs that the buyer's existing accounts allow: enter through the cashback portal link the buyer already uses, activate card-linked or loyalty offers, clip coupons on the retailer's coupon page. Then select the purchase path, **clip every coupon that renders after it** (some appear only once a subscription is selected), and enter each code in the cart. If a discount depends on the payment method, check that the selected method earns it; changing the method is the buyer's call. For value the final page cannot show (portal cashback, card-linked offers), record that it was activated and is pending.
3. **Stop on the final page and verify by scoped extraction**: only the intended item and quantity (if anything else from the cart is in the order, stop and ask, and never remove the buyer's own items); the items line at the expected price; **every expected discount line present**; the charged total inside the expected range; a delivery promise and fulfillment that still meet the buyer's needs; a matching destination; and the confirmation boxes the page requires. Tick a subscription's future-payment acknowledgement only when the instruction covered buying the subscription. A discount the product page advertised but the final page does not show has not been applied: fix it or report it, do not click.
4. **Click the one visible submitting control once.** Never retry blindly. If the page does not advance, read its own objections, then check order history before anything else.
5. **Confirm in order history** by scoped extraction (order number, item line, discount lines, total) and, for a subscription, in the subscription list (next delivery date). A thank-you page is a hint, not proof.
6. **Restore side effects.** Remove what the run added to the cart relative to the step 1 baseline, then verify the removal.
7. **A correction after purchase.** When the buyer names the purchase they wanted instead (one-time versus subscription, another path), that is the instruction for both the cancellation and the replacement; otherwise state both, with the option and expected total, and wait. Take the replacement to its final page first and confirm its total is lower with any single-use discount still available; then cancel before shipment; then place it; then confirm by scoped extraction that the original payment hold was released, or ask the buyer to check.

## When the final click moves to the buyer

Hand over the stack with it: the purchase path to select, the coupons to clip, the codes to enter, the portal link to start from, and the discount lines and total the final page must show. Without that, the buyer's own checkout falls back to the plain one-time path.

## Failure signatures seen at checkout

Properties of a checkout flow or retailer class that hold regardless of who is shopping or for what. Never a product, price, region, ZIP, order, account state (balances, memberships, payment method) or purchase date. A new checkout observation goes to the private `live-runs.jsonl` first (SKILL.md Step 7) and is promoted here only when it recurs, with those details stripped.

- **Fake out-of-stock for an automation-flagged browser.** Checkout can answer "out of stock" for every item while the product page and the cart say in stock at the same minute. Test it with an unrelated control item taken only to the final page: never submit it, remove it from the cart afterwards and verify the removal. If the control also fails, the refusal is about the browser, not the inventory. A browser that is not automation-flagged gets through with the same session; otherwise hand the final click to the buyer with the stack, as above.
- **A subscription that will not confirm.** The confirm button can do nothing until the future-payment acknowledgement is ticked. Nothing on the page says so; the box sits in the payment section.
- **Duplicate submit controls.** Several same-named buttons can exist with only some visible; clicking a hidden one waits and times out without effect. Act only on a visible control.
- **Store credit can zero the order total.** A gift-card or store-credit balance is the buyer's money, not a discount, and it is applied automatically, so the line labelled as the order total can read zero. Check the amount before credit, and report which kind of balance paid.

## What the report says afterwards

The order number, quantity, items line, each discount line with its CONSTITUTION I.5 mark, tax, the charged total, what paid it (store credit or card, with no card details), the delivery promise, any pending value paid later, and for a subscription its interval, next delivery and charge date and how to cancel; then any cart or order cleanup performed, and the purchases ledger row or the reason the write was refused.

Write one row per order action (placed, cancelled, replaced, returned) by piping it to `python scripts/ledger.py append purchases --row-file - --config-dir <root>`, never through a file inside this repository. The row names the selected root's `profile_id` (the writer never fills it in) and has `ts`, `retailer`, `order_ref`, `item`, `path` (`one-time`, `subscription`, `multi-pack`), `quantity`, `charged_total` and `status` (`placed`, `cancelled`, `replaced`, `returned`), plus as known `variant_key`, `items_total`, `tax`, `paid_with` (`store-credit`, `card`, `mixed`, `other`), `discounts` as `{type, amount, mark}` with the I.5 mark (`cart_tested`, `unverified`, `expired_failed`, `paid_later`), `subscription` as `{interval, next_delivery}` with an interval such as `6-weeks` or `2-months` and the next delivery required while it is placed, `replaced_by` on a replaced order only, and `notes`. Without a conforming profile there is no ledger to write: report the row in the reply. [CONFIG.md](../../../CONFIG.md#ledgers) is the full definition.
