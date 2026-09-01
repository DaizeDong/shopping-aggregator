#!/usr/bin/env python3
"""Card-scoped flight price probe: Google Flights (server-rendered) plus a Skiplagged cross-check.

WHY THIS FILE EXISTS
--------------------
A real run priced a transpacific one-way off Google Flights and reported a nonstop at USD 551
that was actually USD 652, and a second nonstop at USD 472 that was actually USD 785. The
itineraries were read correctly. The prices were not, and the failure mode is the whole point:

    the parser matched a price to an itinerary by PROXIMITY, taking the nearest
    aria-label="NNN US dollars" that followed the itinerary= token.

Google Flights does not price every card. A card it cannot price renders the literal string
"Price unavailable" and carries no price node at all. The proximity parser therefore walked past
that card (measured distance: 33,252 bytes) and stapled a different card's price onto it. Two
independent snapshots agreed with each other, because a deterministic bug reproduces exactly like
a stable measurement. Nothing in the output distinguished a price that was read from one that was
invented.

THE INVARIANT THIS MODULE ENFORCES
----------------------------------
    A price belongs to an itinerary ONLY if both live inside the same <li> card.

There is no fallback, no nearest match, no widening radius. A card with no price node yields
price=None and price_unavailable=True, and callers must render that as "price unavailable". They
must never drop the row (an unpriced nonstop is a real option worth naming) and never borrow a
neighbour's number. That is a fix to the FRAMING, meaning what counts as evidence that a number
belongs to a flight, rather than to the symptom, meaning one wrong figure.

selftest() is a NEGATIVE control: it fails if a price ever attaches across a card boundary. A test
that can only pass proves nothing, so it is built to fail on the exact historical defect.

USAGE
    python flight_probe.py search JFK PEK 2026-11-09
    python flight_probe.py search JFK PEK 2026-11-09 --max-stops 1 --max-hours 24
    python flight_probe.py sweep  JFK PEK 2026-11-01 2026-11-12
    python flight_probe.py cross  JFK PEK 2026-11-09
    python flight_probe.py sellers JFK PEK 2026-11-09 KE86+KE851
    python flight_probe.py selftest

EVIDENCE GRADE
    Everything here is E2 (metasearch). Reaching E1 means the airline's own booking page.
    Google Flights server HTML carries NO fare-brand and NO baggage attribute anywhere, so a fare
    bucket can never be inferred from these numbers. See reference/domains/air-travel.md.
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import html as _html
import json
import re
import sys
import time
import urllib.request

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SEAT = {"economy": 1, "premium": 2, "business": 3, "first": 4}
TRIP = {"oneway": 2, "roundtrip": 1}


# --------------------------------------------------------------------- query encoding

def _varint(n: int) -> bytes:
    out = b""
    while True:
        chunk = n & 0x7F
        n >>= 7
        out += bytes([chunk | 0x80]) if n else bytes([chunk])
        if not n:
            return out


def _tag(num: int, wire: int) -> bytes:
    return _varint((num << 3) | wire)


def _blob(num: int, val) -> bytes:
    if isinstance(val, str):
        val = val.encode()
    return _tag(num, 2) + _varint(len(val)) + val


def _num(num: int, val: int) -> bytes:
    return _tag(num, 0) + _varint(val)


def build_tfs(date: str, origin: str, dest: str, seat: str = "economy",
              trip: str = "oneway", adults: int = 1, max_stops=None) -> str:
    """Google Flights encodes the entire query as a base64url protobuf in the tfs param."""
    leg = _blob(2, date) + _blob(13, _blob(2, origin)) + _blob(14, _blob(2, dest))
    if max_stops is not None:
        leg += _num(5, max_stops)
    info = _blob(3, leg) + _num(9, SEAT[seat]) + _blob(8, _num(1, 1)) * adults + _num(19, TRIP[trip])
    return base64.urlsafe_b64encode(info).decode().rstrip("=")


def gf_url(date: str, origin: str, dest: str, currency: str = "USD",
           locale: str = "en", region: str = "us", **kw) -> str:
    return ("https://www.google.com/travel/flights"
            f"?tfs={build_tfs(date, origin, dest, **kw)}"
            f"&hl={locale}&gl={region}&curr={currency}&tfu=EgQIABABIgA")


# --------------------------------------------------------------------------- fetch

class FetchError(RuntimeError):
    """A transport could not produce a usable document.

    Deliberately loud. "could not fetch" and "fetched, found nothing" must never collapse into
    the same empty list, which is exactly how an unreached channel starts reading as an empty
    market. Callers catch this and record a typed coverage gap.
    """


class ParseError(RuntimeError):
    """A document was fetched but a field failed to parse across the whole document.

    Second failure of the same family as the proximity bug, found by an adversarial reviewer.
    `usable()` drops any row whose duration exceeds the limit, and an UNPARSED duration compares
    as infinite, so it drops too. Run the same query under --locale zh-CN and every aria-label
    localizes, every duration parses empty, every row is discarded, and the output reads
    "the Chinese market has nothing." It was a parser artifact wearing a market fact's clothes.

    The rule that closes it: FAILING TO MEASURE IS NOT MEASURING AND FAILING. When a field is
    absent from every priced row, that is a broken instrument, and it must raise here rather
    than quietly shrink the result set.
    """


def fetch(url: str, tries: int = 3, min_bytes: int = 300_000, timeout: int = 90) -> str:
    last = None
    for attempt in range(tries):
        try:
            raw = urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout
            ).read().decode("utf-8", "replace")
            if len(raw) >= min_bytes:
                return raw
            last = f"short document ({len(raw)} bytes, wanted at least {min_bytes})"
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(4 * (attempt + 1))
    raise FetchError(f"{url} -> {last}")


# --------------------------------------------------------------------------- parse

_LI = re.compile(r"<li\b", re.I)
_ITIN = re.compile(r'itinerary=([A-Z0-9,\-]+)"')
_PRICE = re.compile(r'aria-label="([\d,]+) (?:US dollars|人民币|euros|pounds|yen)"')
# Google localizes every aria-label. Patterns are best effort across locales; correctness does
# NOT rest on this list being complete, it rests on the all-rows-unparsed gate below.
_DUR = re.compile(r'aria-label="(?:Total duration|Duree totale|Dauer insgesamt|Duracion total|'
                  r'总时长|總時長|所要時間) ?[: ]?([^"]+?)[.。]?"')
_DEP = re.compile(r'aria-label="(?:Departure time|Heure de depart|Abflugzeit|Hora de salida|'
                  r'出发时间|出発時間)[: ]\s*([^"]+?)"')
_ARR = re.compile(r'aria-label="(?:Arrival time|Heure d.arrivee|Ankunftszeit|Hora de llegada|'
                  r'到达时间|到着時間)[: ]\s*([^"]+?)"')
_UNAVAILABLE = "Price unavailable"


def _clean(match):
    if not match:
        return None
    return _html.unescape(match.group(1)).replace(" ", " ").strip()


def _card_spans(doc: str):
    """Yield (start, end) for each <li> card. These cards do not nest in this markup."""
    starts = [m.start() for m in _LI.finditer(doc)]
    for i, start in enumerate(starts):
        following = starts[i + 1] if i + 1 < len(starts) else len(doc)
        close = doc.find("</li>", start)
        yield start, (min(following, close + 5) if close > 0 else following)


def parse_cards(doc: str) -> list:
    """Card-scoped extraction. THE invariant: a price and its itinerary share one <li>."""
    rows, seen = [], set()
    for start, end in _card_spans(doc):
        block = doc[start:end]
        tokens = _ITIN.findall(block)
        if not tokens:
            continue
        token = tokens[0]
        segments = [p.split("-") for p in token.split(",")]
        segments = [p for p in segments if len(p) >= 5]
        if not segments:
            continue

        # Prices come from THIS block and nowhere else. No widening, ever.
        prices = [int(x.replace(",", "")) for x in _PRICE.findall(block)]
        price = min(prices) if prices else None
        unavailable = _UNAVAILABLE in block

        row = {
            "price": price,
            "price_unavailable": price is None and unavailable,
            "price_missing": price is None and not unavailable,
            "flights": "+".join(f"{p[2]}{p[3]}" for p in segments),
            "carriers": "/".join(dict.fromkeys(p[2] for p in segments)),
            "route": "-".join([segments[0][0]] + [p[1] for p in segments]),
            "stops": len(segments) - 1,
            "duration": _clean(_DUR.search(block)),
            "duration_unparsed": _DUR.search(block) is None,
            "depart": _clean(_DEP.search(block)),
            "arrive": _clean(_ARR.search(block)),
            "token": token,
        }
        key = (row["flights"], row["price"], row["price_unavailable"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    rows.sort(key=lambda r: (r["price"] is None, r["price"] or 0))
    return rows


_H_UNITS = r"(?:hr|hrs|hour|hours|h|Std|Stunden|heure|heures|小时|小時|時間)"
_M_UNITS = r"(?:min|mins|minute|minutes|m|Min|Minuten|分钟|分鐘|分)"


def duration_hours(text) -> float:
    """Hours, or inf when the duration is UNKNOWN. Never 0 for text that failed to parse.

    Third member of the same failure family as the proximity bug and the locale drop. The
    original returned `0 + 0/60` whenever neither unit matched, so a localized "30 小时 40 分钟"
    scored as ZERO HOURS and a 35-hour itinerary sailed through a 24-hour filter as the shortest
    thing on the page. Parsing nothing must never be reported as measuring zero.
    """
    if not text:
        return float("inf")
    hours = re.search(r"(\d+)\s*" + _H_UNITS, text)
    mins = re.search(r"(\d+)\s*" + _M_UNITS, text)
    if not hours and not mins:
        return float("inf")
    return (int(hours.group(1)) if hours else 0) + (int(mins.group(1)) if mins else 0) / 60


def usable(rows, max_stops: int = 1, max_hours: float = 24.0, strict: bool = True) -> list:
    """Rows a traveller would actually consider. Priced rows only, never a borrowed price.

    Raises ParseError when EVERY priced row lost its duration, because that is an instrument
    failure and returning [] would present it as an empty market. Pass strict=False only when
    the caller has already decided to treat unparsed durations as unknown-but-reportable.
    """
    priced = [r for r in rows if r["price"]]
    if priced and all(r.get("duration_unparsed") or duration_hours(r["duration"]) == float("inf")
                      for r in priced):
        raise ParseError(
            f"all {len(priced)} priced rows have an unparsed duration: the duration label did not "
            "match, most likely a locale this build has no pattern for. Refusing to return an "
            "empty result set that would read as an empty market. Re-run with --locale en, or add "
            "the locale's label to _DUR."
        )
    return [r for r in priced
            if r["stops"] <= max_stops and duration_hours(r["duration"]) <= max_hours]


def filter_report(rows, max_stops: int = 1, max_hours: float = 24.0):
    """(kept, dropped_long, dropped_unknown_duration, dropped_unpriced). Nothing vanishes silently."""
    kept, long, unknown, unpriced = [], [], [], []
    for r in rows:
        if not r["price"]:
            unpriced.append(r)
        elif r.get("duration_unparsed") or duration_hours(r["duration"]) == float("inf"):
            unknown.append(r)
        elif r["stops"] > max_stops or duration_hours(r["duration"]) > max_hours:
            long.append(r)
        else:
            kept.append(r)
    return kept, long, unknown, unpriced


# ------------------------------------------------------------------- absence states

NO_INVENTORY = "no_inventory"      # the market really has none of this
NOT_PRICED = "not_priced"          # the offer exists, this channel declines to price it
NOT_FETCHED = "not_fetched"        # the query did not come back healthy; says nothing about the market

HEALTHY_CARDS = 10


def channel_health(rows, floor: int = HEALTHY_CARDS) -> str:
    """Is this document evidence about the market, or evidence about the fetch?

    A flight query is nondeterministic per pull, and an empty or near-empty result is the MODAL
    ARTIFACT rather than the modal fact. Observed in one run: a sweep printed "nothing usable" for a
    date whose two immediate re-fetches both returned a 530 fare; another pair returned 0 cards once
    and 139 on retry; an aggregator omitted a nonstop on three dates and produced it on a second pull.
    Every one of those, believed once, becomes a false schedule claim.

    So a thin document is NOT_FETCHED, never NO_INVENTORY. Only a healthy document can carry an
    absence, and even then `absence_verdict` wants two of them.
    """
    return NOT_FETCHED if len(rows) < floor else "healthy"


def absence_verdict(observations, predicate) -> str:
    """Classify an absence across N independent fetches. Requires TWO healthy agreeing pulls.

    observations: list of row-lists, one per independent fetch.
    predicate:    rows -> True when the thing being looked for IS present.

    Returns NO_INVENTORY only when at least two healthy fetches agree it is absent. One healthy
    fetch, or any number of thin ones, returns NOT_FETCHED. If any fetch found it, it is present and
    this is not an absence at all.
    """
    healthy = [rows for rows in observations if channel_health(rows) == "healthy"]
    if any(predicate(rows) for rows in observations):
        return "present"
    if len(healthy) >= 2:
        return NO_INVENTORY
    return NOT_FETCHED


# ----------------------------------------------------------------------- skiplagged

_SK = ("https://skiplagged.com/api/search.php"
       "?from={o}&to={d}&depart={date}&return=&format=v3"
       "&counts%5Badults%5D=1&counts%5Bchildren%5D=0")


def _sk_payload(origin: str, dest: str, date: str, tries: int = 4) -> dict:
    """The first call commonly warms a cache and returns a stub, so retry until legs appear.

    Repeated calls return the SAME cached snapshot, so the result is ONE observation, not N.
    Do not fire these in parallel; the endpoint answers a burst with a Cloudflare challenge.
    """
    url = _SK.format(o=origin, d=dest, date=date)
    last = None
    for _ in range(tries):
        try:
            payload = json.loads(urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=60).read().decode())
            if payload.get("itineraries", {}).get("outbound"):
                return payload
            last = "no outbound itineraries in payload"
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(4)
    raise FetchError(f"skiplagged {origin}-{dest} {date} -> {last}")


def skiplagged(origin: str, dest: str, date: str) -> dict:
    """Second transport. Returns {flight_key: cents}."""
    payload = _sk_payload(origin, dest, date)
    flights, out = payload.get("flights", {}), {}
    for leg in payload["itineraries"]["outbound"]:
        info, cents = flights.get(leg["flight"]), leg.get("one_way_price")
        if not info or not cents:
            continue
        key = "+".join(f"{s['airline']}{s['flight_number']}" for s in info["segments"])
        if key not in out or cents < out[key]:
            out[key] = cents
    return out


def sellers(origin: str, dest: str, date: str, flight_key: str) -> dict:
    """Per-OTA prices behind ONE itinerary, so "the public price" is reported as a BAND.

    Anchoring a discount claim on a single metasearch headline overstates it: the same seat is
    commonly retailed across a 10 percent spread by different sellers.
    """
    payload = _sk_payload(origin, dest, date)
    flights, found = payload.get("flights", {}), {}
    for leg in payload["itineraries"]["outbound"]:
        info = flights.get(leg["flight"])
        if not info:
            continue
        key = "+".join(f"{s['airline']}{s['flight_number']}" for s in info["segments"])
        if key != flight_key:
            continue
        blob = re.search(r"\{.*\}", leg.get("data", ""))
        if not blob:
            continue
        for src in json.loads(blob.group(0)).get("source", []):
            for name, val in src.get("source", {}).items():
                cents = val[1] if isinstance(val, list) and len(val) > 1 else src.get("cost")
                if cents:
                    found[name] = min(found.get(name, 1e9), cents / 100)
    return found


# ------------------------------------------------------------------------- selftest

_SYNTHETIC = """
<ul>
  <li data-card="1">
    <a data-websiteurl="x?itinerary=JFK-PEK-CA-982-20261109"></a>
    <div>Price unavailable</div>
    <div aria-label="Total duration 16 hr 45 min."></div>
  </li>
  <li data-card="2">
    <a data-websiteurl="x?itinerary=JFK-SEA-AS-21-20261109,SEA-ICN-AS-119-20261109"></a>
    <span aria-label="492 US dollars">$492</span>
    <div aria-label="Total duration 26 hr 15 min."></div>
  </li>
  <li data-card="3">
    <a data-websiteurl="x?itinerary=JFK-ICN-KE-86-20261109,ICN-PEK-KE-851-20261110"></a>
    <span aria-label="563 US dollars">$563</span>
    <div aria-label="Total duration 19 hr 35 min."></div>
  </li>
</ul>
"""


_LOCALIZED = """
<ul>
  <li data-card="1">
    <a data-websiteurl="x?itinerary=JFK-ICN-KE-86-20261109,ICN-PEK-KE-851-20261110"></a>
    <span aria-label="3780 US dollars">CN&#165;3,780</span>
    <div aria-label="Zzz totale 19 Std 35 min."></div>
  </li>
</ul>
"""


def selftest() -> int:
    """Negative control. Asserts the historical regression cannot come back.

    The bug produced CA982 = 492 by reaching into the NEXT card. If any future edit reintroduces
    proximity matching, the first assertion below fires and this exits non-zero.
    """
    rows = {r["flights"]: r for r in parse_cards(_SYNTHETIC)}
    failures = []

    ca = rows.get("CA982")
    if ca is None:
        failures.append("CA982 was dropped; an unpriced flight must still be reported, not hidden")
    else:
        if ca["price"] is not None:
            failures.append(f"REGRESSION: CA982 has no price node yet parsed price={ca['price']}; "
                            "a price leaked across a card boundary")
        if not ca["price_unavailable"]:
            failures.append("CA982 must be flagged price_unavailable rather than silently null")

    alaska = rows.get("AS21+AS119")
    if not alaska or alaska["price"] != 492:
        failures.append(f"the 492 must stay on AS21+AS119, got {alaska and alaska['price']}")

    korean = rows.get("KE86+KE851")
    if not korean or korean["price"] != 563:
        failures.append(f"an in-card price must be read, expected 563 got {korean and korean['price']}")

    if ca and usable([ca], max_stops=0, max_hours=99):
        failures.append("usable() must never surface an unpriced row as rankable")

    if duration_hours("26 hr 15 min") <= 24 or duration_hours(None) != float("inf"):
        failures.append("duration_hours must exclude over-long and unknown durations")
    if abs(duration_hours("30小时 40分钟") - 30.6667) > 0.01:
        failures.append("REGRESSION: a localized duration must parse to its real length, not 0")
    if duration_hours("about a day") != float("inf"):
        failures.append("REGRESSION: an unparseable duration must be inf (unknown), never 0, "
                        "or an over-long itinerary passes a max-hours filter as the shortest row")

    # Gate 2: a whole-document field failure must RAISE, not return an empty market.
    localized = parse_cards(_LOCALIZED)
    if not localized or localized[0]["price"] != 3780:
        failures.append("a priced row must still parse when only its duration label is unknown")
    elif not localized[0]["duration_unparsed"]:
        failures.append("an unmatched duration label must set duration_unparsed")
    else:
        try:
            usable(localized)
            failures.append(
                "REGRESSION: every priced row had an unparsed duration and usable() returned "
                "quietly. A parser artifact is being presented as an empty market.")
        except ParseError:
            pass

    thin = [{"price": 1, "stops": 0, "duration": "1 hr", "duration_unparsed": False}]
    fat = [dict(thin[0]) for _ in range(HEALTHY_CARDS + 5)]
    if channel_health(thin) != NOT_FETCHED:
        failures.append("a thin document must be NOT_FETCHED, never evidence about the market")
    if channel_health(fat) != "healthy":
        failures.append("a full document must read healthy")
    none_here = lambda rows: False
    if absence_verdict([fat], none_here) != NOT_FETCHED:
        failures.append("REGRESSION: one healthy fetch must not be enough to declare no_inventory")
    if absence_verdict([fat, fat], none_here) != NO_INVENTORY:
        failures.append("two healthy agreeing fetches must be allowed to declare no_inventory")
    if absence_verdict([thin, thin, thin], none_here) != NOT_FETCHED:
        failures.append("REGRESSION: repeating a THIN fetch must never manufacture an absence")
    if absence_verdict([fat, fat], lambda rows: True) != "present":
        failures.append("a found item must report present, not an absence")


    kept, long, unknown, unpriced = filter_report(
        [{"price": 500, "stops": 0, "duration": "10 hr", "duration_unparsed": False},
         {"price": 500, "stops": 0, "duration": "40 hr", "duration_unparsed": False},
         {"price": 500, "stops": 0, "duration": None, "duration_unparsed": True},
         {"price": None, "stops": 0, "duration": "10 hr", "duration_unparsed": False}])
    if (len(kept), len(long), len(unknown), len(unpriced)) != (1, 1, 1, 1):
        failures.append(f"filter_report must account for every row, got "
                        f"{len(kept)}/{len(long)}/{len(unknown)}/{len(unpriced)}")

    if failures:
        for line in failures:
            print(f"FAIL  {line}")
        return 1
    print("PASS  16 assertions: no cross-card price leak, unpriced row preserved and flagged, "
          "in-card price read, unpriced row not rankable, duration filter sound, "
          "unknown-duration row still parsed and flagged, whole-document field failure raises "
          "instead of returning an empty market, filter_report accounts for every row, "
          "localized duration parses to its real length, unparseable duration is unknown "
          "not zero, thin document is not_fetched, full document is healthy, one healthy "
          "fetch cannot declare an absence, two agreeing can, repeating a thin fetch never "
          "manufactures one, a hit reports present")
    return 0


# ------------------------------------------------------------------------------ cli

def _render(rows, limit=25):
    print(f"{'price':>12}  {'flights':<24} {'route':<20} {'st':<3} {'duration':<14} departs")
    for row in rows[:limit]:
        if row["price"] is not None:
            price = f"{row['price']:,}"
        elif row["price_unavailable"]:
            price = "unavailable"
        else:
            price = "no price node"
        print(f"{price:>12}  {row['flights']:<24} {row['route']:<20} {row['stops']:<3} "
              f"{str(row['duration'] or ''):<14} {row['depart'] or ''}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Card-scoped flight price probe.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    search = sub.add_parser("search")
    search.add_argument("origin"); search.add_argument("dest"); search.add_argument("date")
    search.add_argument("--currency", default="USD")
    search.add_argument("--seat", default="economy")
    search.add_argument("--region", default="us")
    search.add_argument("--locale", default="en")
    search.add_argument("--max-stops", type=int)
    search.add_argument("--max-hours", type=float)
    search.add_argument("--json", action="store_true")

    sweep = sub.add_parser("sweep")
    sweep.add_argument("origin"); sweep.add_argument("dest")
    sweep.add_argument("start"); sweep.add_argument("end")
    sweep.add_argument("--currency", default="USD")

    cross = sub.add_parser("cross")
    cross.add_argument("origin"); cross.add_argument("dest"); cross.add_argument("date")

    sell = sub.add_parser("sellers")
    sell.add_argument("origin"); sell.add_argument("dest")
    sell.add_argument("date"); sell.add_argument("flight_key")
    sell.add_argument("--currency", default="USD",
                      help="informational only: the Skiplagged seller endpoint is USD-only, "
                           "so a non-USD value is refused rather than silently ignored")

    sub.add_parser("selftest")
    args = parser.parse_args(argv)

    if args.cmd == "selftest":
        return selftest()

    if args.cmd == "search":
        doc = fetch(gf_url(args.date, args.origin, args.dest, currency=args.currency,
                           seat=args.seat, region=args.region, locale=args.locale))
        rows = parse_cards(doc)
        if args.max_stops is not None or args.max_hours is not None:
            kept, long, unknown, unpriced = filter_report(
                rows,
                args.max_stops if args.max_stops is not None else 99,
                args.max_hours if args.max_hours is not None else 1e9)
            if kept == [] and unknown:
                raise ParseError(
                    f"filter kept 0 rows while {len(unknown)} priced rows had an UNPARSED "
                    "duration. That is an instrument failure, not an empty market. Re-run with "
                    "--locale en or teach _DUR this locale's label.")
            if unknown or long or unpriced:
                print(f"# filtered out: {len(long)} too long or too many stops, "
                      f"{len(unknown)} with an unparsed duration (NOT the same as too long), "
                      f"{len(unpriced)} unpriced", file=sys.stderr)
            rows = kept
        if args.json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            _render(rows)
        return 0

    if args.cmd == "sweep":
        day = _dt.date.fromisoformat(args.start)
        last = _dt.date.fromisoformat(args.end)
        while day <= last:
            iso = day.isoformat()
            try:
                rows = parse_cards(fetch(gf_url(iso, args.origin, args.dest, currency=args.currency)))
                if channel_health(rows) == NOT_FETCHED:
                    print(f"{iso}  NOT_FETCHED: only {len(rows)} cards parsed, below the health "
                          f"floor of {HEALTHY_CARDS}. This says nothing about the market; re-run "
                          "this date before recording any absence.")
                    day += _dt.timedelta(days=1)
                    time.sleep(2)
                    continue
                good = usable(rows)
                nonstop = [r for r in rows if r["stops"] == 0]
                head = " | ".join(f"{r['price']:,} {r['flights']} {r['duration']}"
                                  for r in good[:2]) or "nothing under 24h with 1 stop"
                tail = "   nonstop: " + (", ".join(
                    f"{r['flights']} " + (f"{r['price']:,}" if r["price"] else NOT_PRICED)
                    for r in nonstop) or "none in THIS pull (one healthy fetch is not an absence, "
                                          "re-run before calling it no_inventory)")
                print(f"{iso}  {head}{tail}")
            except FetchError as exc:
                print(f"{iso}  FETCH FAILED: {exc}")
            day += _dt.timedelta(days=1)
            time.sleep(2)
        return 0

    if args.cmd == "cross":
        google = {r["flights"]: r for r in parse_cards(fetch(gf_url(args.date, args.origin, args.dest)))}
        other = skiplagged(args.origin, args.dest, args.date)
        print(f"{'flights':<24} {'google':>12} {'skiplagged':>12}   verdict")
        for key in sorted(set(google) | set(other)):
            left = google.get(key, {}).get("price")
            right = other.get(key)
            if left and right:
                gap = abs(left - right / 100) / max(left, right / 100)
                verdict = "agree" if gap <= 0.05 else f"DISAGREE {gap * 100:.0f} pct, re-fetch, never average"
            elif left or right:
                verdict = "one transport only"
            else:
                verdict = "unpriced on both"
            print(f"{key:<24} {(f'{left:,}' if left else '-'):>12} "
                  f"{(f'{right / 100:,.0f}' if right else '-'):>12}   {verdict}")
        return 0

    if args.cmd == "sellers":
        if args.currency.upper() != "USD":
            print("the Skiplagged seller endpoint returns USD only; refusing rather than "
                  "returning USD figures labelled as another currency", file=sys.stderr)
            return 2
        band = sellers(args.origin, args.dest, args.date, args.flight_key)
        if not band:
            print(f"no seller breakdown for {args.flight_key}; treat as a coverage gap, not a zero")
            return 0
        print(f"public seller band for {args.flight_key} on {args.date}:")
        for name, price in sorted(band.items(), key=lambda kv: kv[1]):
            print(f"   {name:<16} {price:,.2f}")
        low, high = min(band.values()), max(band.values())
        print(f"   band {low:,.2f} to {high:,.2f}  "
              f"(spread {(high - low) / low * 100:.1f} pct; anchor a discount on the LOW end)")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
