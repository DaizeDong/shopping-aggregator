"""Schemas for a config root: profile.json, forwarder tables and the run ledgers.

CONFIG.md documents these fields for people; this module enforces them. The doctor
(scripts/verify_config.py), the ledger writer (scripts/ledger.py), verify_matrix and the tests all
call the same functions, so there is one definition of a valid config instead of one per caller.

Validators return problems as (field_path, message) pairs; live-run rows add a severity in front.
A message never includes the offending value, and a path names a key only when the key itself is
safe to print: the inputs are a real person's settings, and a doctor that echoes them turns every
log into a copy of the profile. Validators never raise on malformed input. A wrong type is a
problem like any other, so one bad field cannot hide the report on every other field.
"""
import datetime
import json
import math
import re

PROFILE_SCHEMA_VERSION = 1
MAX_DEPTH = 32

KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
COUNTRY = re.compile(r"[A-Z]{2}")
REGION = re.compile(r"[A-Z0-9]{1,3}(?:-[A-Z0-9]{1,3})?")
POSTAL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 -]{1,9}")
CURRENCY = re.compile(r"[A-Z]{3}")
LOCALE = re.compile(r"[a-z]{2}-[A-Z]{2}")
IATA = re.compile(r"[A-Z]{3}")
ZONE_ID = re.compile(r"[A-Za-z0-9-]{1,10}")
DIGITS = re.compile(r"\d{1,5}")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
TIMESTAMP = re.compile(r"(\d{4}-\d{2}-\d{2})(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2}))?")
INTERVAL = re.compile(r"[1-9]\d{0,2}-(?:day|week|month)s?")
SESSION = re.compile(r"[a-z0-9-]+:[a-z0-9-]+")

SUBSCRIPTIONS = {"accept-fee-free", "ask", "decline"}
CHECKOUT = {"agent", "owner-browser", "none"}
CABINS = {"economy", "premium-economy", "business", "first"}

# A profile holds what changes a price or a route, never who the person is. Every object in it has
# a closed set of fields, so the only free keys are preference categories, and ordinary category
# words must stay usable there: rolling-pin, passport-cover, victorias-secret, credit-card,
# no-store-card. A key name is refused only when its words, read together, label a credential or
# an identity number; contact, payment and address DATA is caught by its shape wherever it
# appears, in values and in keys alike.
CREDENTIAL_WORDS = {"password", "passwd", "pwd", "passcode", "cvv", "cvc", "ssn", "iban", "dob",
                    "birthdate", "credential", "credentials"}           # never a shopping category
LABEL_WORDS = {"pin", "secret", "token", "passport", "routing", "auth"}  # a label only when alone
QUALIFIER_WORDS = {"my", "the", "bank", "atm", "debit", "credit", "visa", "amex", "mastercard",
                   "primary", "secondary", "backup", "login", "online", "api", "access", "user",
                   "account", "card", "gift", "social", "security", "date", "of", "id", "driver",
                   "drivers", "tax"}
NUMBER_WORDS = {"number", "num", "no", "code", "key"}
NUMBERED_THINGS = {"card", "account", "security", "id", "api", "access"}
EMAIL_VALUE = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")
NUMBER_RUN = re.compile(r"\d[\d\s().+/-]*\d")
# Unambiguous suffixes match whatever the case; suffixes that are also common words (way, loop,
# square, circle) only after a capitalized street name, so "2 pack any way works" stays a preference.
_STREET_NAME = r"(?:[A-Za-z0-9.'-]+\s+){1,3}"
_CAPITALIZED_NAME = r"(?:[A-Z][A-Za-z0-9.'-]*\s+){1,3}"
_NUMBER = r"\b(?:\d{1,6}[A-Za-z]?,?|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
STREET_VALUE = re.compile(
    _NUMBER + _STREET_NAME + r"(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|ct|"
    r"court|pl|place|pkwy|parkway|ter|terrace|hwy|highway)\b", re.I)
STREET_CAPITALIZED = re.compile(
    r"(?i:" + _NUMBER + r")" + _CAPITALIZED_NAME + r"(?:Way|Circle|Cir|Plaza|Plz|Square|Sq|Trail|Trl|Loop|"
    r"Path|Pike|Row|Run|Walk|Alley|Crescent|Cres|Point|Ridge|Heights|Hts|Park|Gardens|Grove|Close|Mews|"
    r"Bend|Cove|Crossing|Xing|Route|Rte|Expressway|Turnpike|Tpke)\b")
STREET_NUMBER_AFTER = re.compile(
    r"\b" + _CAPITALIZED_NAME + r"(?:Street|St|Road|Rd|Avenue|Ave|Way|Strasse|Straße|Gasse|Weg)\.?\s+\d{1,5}\b")
PO_BOX = re.compile(r"\bP\.?\s*O\.?\s*Box\s+\d+", re.I)
US_ZIP = re.compile(r"\d{5}(?:-\d{4})?")
HOSTNAME = re.compile(r"(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")
SECRET_VALUE = re.compile(r"(?=[A-Za-z0-9_+/=-]*\d)(?=[A-Za-z0-9_+/=-]*[A-Za-z])[A-Za-z0-9_+/=-]{32,}")
DATE_ONLY = re.compile(r"\s*(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{2,4})\s*")
SAFE_KEY = re.compile(r"[A-Za-z0-9_-]{1,40}")

PROFILE_FIELDS = {
    "schema_version", "profile_id", "label", "market", "ship_to", "memberships", "not_held",
    "store_credit", "purchase_defaults", "risk", "accounts", "home_stores", "travel", "off_limits",
    "forwarders", "preferences",
}
MARKET_FIELDS = {"country", "currency", "locale"}
SHIP_TO_FIELDS = {"zip", "state", "city", "effective_from"}
MEMBERSHIP_FIELDS = {"program", "tier", "perks", "cash_back_pct", "confirmed_on"}
DEFAULTS_FIELDS = {"subscriptions", "subscription_interval"}
RISK_FIELDS = {"marketplace_min_rating_pct", "marketplace_min_ratings", "deep_depth_usd"}
ACCOUNT_FIELDS = {"retailer", "session", "checkout", "identity"}
HOME_STORE_FIELDS = {"retailer", "store"}
TRAVEL_FIELDS = {"home_airports", "cabin", "checked_bags", "payment_currency", "hotel_adults"}
FORWARDER_FIELDS = {"name", "zone", "duty_inclusive", "rate_table"}

FORWARDER_TABLE_FIELDS = {"schema_version", "name", "currency", "duty_inclusive", "zone_by", "zones",
                          "classes", "volumetric_divisor_cm", "min_billable_kg", "notes", "source",
                          "verified_date"}
ZONE_BY = {"zip-first-digit"}

LIVE_RUN_REQUIRED = {"ts", "domain", "source", "outcome", "detail", "user_correction"}
OUTCOMES = {"created", "verified", "unverifiable", "dead", "fallback_used", "price_mismatch",
            "coupon_fake", "coverage_gap"}
GAP_REASONS = {"session-gated-declined", "session-gated-unattended", "structurally-unreachable",
               "tool-outage", "not-attempted"}

PURCHASE_REQUIRED = {"ts", "profile_id", "retailer", "order_ref", "item", "path", "quantity",
                     "charged_total", "status"}
PURCHASE_FIELDS = PURCHASE_REQUIRED | {"variant_key", "items_total", "tax", "discounts", "paid_with",
                                       "replaced_by", "subscription", "notes"}
PURCHASE_PATHS = {"one-time", "subscription", "multi-pack"}
PURCHASE_STATUS = {"placed", "cancelled", "replaced", "returned"}
PAID_WITH = {"store-credit", "card", "mixed", "other"}
DISCOUNT_MARKS = {"cart_tested", "unverified", "expired_failed", "paid_later"}


class JSONFormatError(ValueError):
    """A JSON format error whose message contains no input values."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise JSONFormatError("duplicate object key")
        result[key] = value
    return result


def _reject_constant(_value):
    raise JSONFormatError("nonstandard JSON numeric constant")


def loads_strict(text):
    """Parse JSON refusing duplicate keys and NaN/Infinity, which the stdlib accepts silently."""
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def load_strict_json(path):
    """Load a config file strictly. Raises OSError, ValueError (incl. decode errors) or RecursionError."""
    with open(path, "r", encoding="utf-8-sig") as stream:
        return loads_strict(stream.read())


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _string(value, pattern=None):
    """A non-blank string, fully matching pattern when one is given."""
    if not isinstance(value, str) or not value.strip():
        return False
    return pattern is None or pattern.fullmatch(value) is not None


def _member(value, options):
    return isinstance(value, str) and value in options


def valid_date(value):
    if not _string(value, DATE):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def valid_timestamp(value):
    match = TIMESTAMP.fullmatch(value) if isinstance(value, str) else None
    if not match or not valid_date(match.group(1)):
        return False
    if len(value) == 10:
        return True
    try:
        datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def rate_table_ok(value):
    """A rate_table must be a plain path relative to the config root."""
    if not _string(value) or value.startswith(("/", "\\")) or ":" in value:
        return False
    return ".." not in value.replace("\\", "/").split("/")


def _value_problem(text):
    if EMAIL_VALUE.search(text):
        return "looks like an email address; store a label instead"
    for run in NUMBER_RUN.finditer(text):
        if sum(ch.isdigit() for ch in run.group(0)) >= 9:
            return "looks like a phone, card, account or routing number; never store it here"
    if (STREET_VALUE.search(text) or STREET_CAPITALIZED.search(text) or STREET_NUMBER_AFTER.search(text)
            or PO_BOX.search(text)):
        return "looks like a street address or PO box; keep only ZIP, state and city"
    if SECRET_VALUE.search(text):
        return "looks like a credential, token or cookie; never store it here"
    return None


def _key_problem(key):
    if _value_problem(key):
        return "a field name may not carry personal data"
    if names_a_credential(key):
        return "names a credential or identity number; a profile never holds one"
    return None


def names_a_credential(key):
    """Whether a key's words, read together, label a credential or an identity number."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key).lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", spaced) if token]
    words = set(tokens)
    rest = words - QUALIFIER_WORDS - NUMBER_WORDS
    if words & CREDENTIAL_WORDS:                                  # wifi-password, cvv, ssn
        return True
    if rest and rest <= LABEL_WORDS:                              # pin, atm-pin, passport-number
        return True
    if rest == {"birth"} and "date" in words:                     # date-of-birth
        return True
    if rest == {"license"} and words & NUMBER_WORDS:              # drivers-license-number
        return True
    return not rest and bool(words & NUMBER_WORDS) and bool(words & NUMBERED_THINGS)  # card-number


def key_label(key):
    """How a key appears in a report: itself when that is safe to print, else a placeholder."""
    if isinstance(key, str) and SAFE_KEY.fullmatch(key) and _value_problem(key) is None:
        return key
    return "<key>"


def _join(path, key):
    label = key_label(key)
    return "%s.%s" % (path, label) if path else label


def _scan_private(node, path, problems, depth=0, skip=lambda path: False):
    """Refuse identity, contact and payment data anywhere in the tree, by key and by value shape.

    skip(path) exempts a value whose own field validates its shape more precisely: a ZIP+4 is nine
    digits, and a table path may be long; neither is a phone number or a token.
    """
    if depth > MAX_DEPTH:
        problems.append((path or "document", "nested too deeply"))
        return
    if isinstance(node, dict):
        for key, value in node.items():
            child = _join(path, key)
            reason = _key_problem(key) if isinstance(key, str) else "field names must be strings"
            if reason:
                problems.append((child, reason))
            _scan_private(value, child, problems, depth + 1, skip)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _scan_private(value, "%s[%d]" % (path, index), problems, depth + 1, skip)
    elif isinstance(node, str) and not skip(path):
        reason = _value_problem(node)
        if reason:
            problems.append((path, "value " + reason))


def _closed(obj, fields, prefix, problems):
    for key in obj:
        if key not in fields:
            problems.append((_join(prefix, key), "unknown field; add it to the schema first"))


def _object(data, key, fields, problems, required=True):
    value = data.get(key)
    if value is None and not required and key not in data:
        return {}
    if not isinstance(value, dict):
        problems.append((key, "required object" if required else "expected object"))
        return {}
    _closed(value, fields, key, problems)
    return value


def _objects(data, key, fields, problems, required=False):
    value = data.get(key)
    if value is None and not required and key not in data:
        return []
    if not isinstance(value, list):
        problems.append((key, "required array (may be empty)" if required else "expected array"))
        return []
    items = []
    for index, item in enumerate(value):
        prefix = "%s[%d]" % (key, index)
        if not isinstance(item, dict):
            problems.append((prefix, "expected object"))
            continue
        _closed(item, fields, prefix, problems)
        items.append((prefix, item))
    return items


def _kebab_list(data, key, problems):
    value = data.get(key)
    if key in data and not (isinstance(value, list) and all(_string(item, KEBAB) for item in value)):
        problems.append((key, "expected an array of kebab-case ids"))


def profile_id_of(data):
    """The profile's id when that one field is valid, whatever else is wrong with the profile."""
    if isinstance(data, dict) and _string(data.get("profile_id"), KEBAB):
        return data["profile_id"]
    return None


def profile_problems(data):
    """Validate a profile.json object. An empty list means it conforms."""
    if not isinstance(data, dict):
        return [("profile", "expected a JSON object")]
    problems = []
    _scan_private(data, "", problems, skip=lambda path: path == "ship_to.zip" or path.endswith(".rate_table"))
    _closed(data, PROFILE_FIELDS, "", problems)

    version = data.get("schema_version")
    if type(version) is not int or version != PROFILE_SCHEMA_VERSION:
        problems.append(("schema_version", "required integer equal to %d" % PROFILE_SCHEMA_VERSION))
    if profile_id_of(data) is None:
        problems.append(("profile_id", "required kebab-case id"))
    if not _string(data.get("label")):
        problems.append(("label", "required non-empty string"))

    market = _object(data, "market", MARKET_FIELDS, problems)
    if not _string(market.get("country"), COUNTRY):
        problems.append(("market.country", "required ISO 3166-1 alpha-2 code"))
    if not _string(market.get("currency"), CURRENCY):
        problems.append(("market.currency", "required ISO 4217 code"))
    if not _string(market.get("locale"), LOCALE):
        problems.append(("market.locale", "required locale such as en-US"))

    ship = _object(data, "ship_to", SHIP_TO_FIELDS, problems)
    if not _string(ship.get("zip"), US_ZIP if market.get("country") == "US" else POSTAL):
        problems.append(("ship_to.zip", "required postal code (in a US market, 12345 or 12345-6789)"))
    if market.get("country") == "US":
        if not _string(ship.get("state"), COUNTRY):
            problems.append(("ship_to.state", "required two-letter state code for a US market"))
    elif "state" in ship and not _string(ship.get("state"), REGION):
        problems.append(("ship_to.state", "expected a region code"))
    if "city" in ship and not _string(ship.get("city")):
        problems.append(("ship_to.city", "expected non-empty string"))
    if not valid_date(ship.get("effective_from")):
        problems.append(("ship_to.effective_from", "required date YYYY-MM-DD"))

    for prefix, item in _objects(data, "memberships", MEMBERSHIP_FIELDS, problems, required=True):
        if not _string(item.get("program"), KEBAB):
            problems.append((prefix + ".program", "required kebab-case program id"))
        if "tier" in item and not _string(item.get("tier"), KEBAB):
            problems.append((prefix + ".tier", "expected kebab-case tier"))
        if "perks" in item and not (isinstance(item["perks"], list)
                                    and all(_string(p, KEBAB) for p in item["perks"])):
            problems.append((prefix + ".perks", "expected an array of kebab-case ids"))
        if "cash_back_pct" in item and not (_is_number(item["cash_back_pct"])
                                            and 0 <= item["cash_back_pct"] <= 100):
            problems.append((prefix + ".cash_back_pct", "expected a number from 0 to 100"))
        if not valid_date(item.get("confirmed_on")):
            problems.append((prefix + ".confirmed_on", "required date YYYY-MM-DD"))
    for key in ("not_held", "store_credit", "off_limits"):
        _kebab_list(data, key, problems)

    defaults = _object(data, "purchase_defaults", DEFAULTS_FIELDS, problems)
    if not _member(defaults.get("subscriptions"), SUBSCRIPTIONS):
        problems.append(("purchase_defaults.subscriptions",
                         "required choice: accept-fee-free, ask or decline"))
    interval = defaults.get("subscription_interval")
    if interval != "page-default" and not _string(interval, INTERVAL):
        problems.append(("purchase_defaults.subscription_interval",
                         "required: page-default, or an interval such as 6-weeks or 2-months"))

    risk = _object(data, "risk", RISK_FIELDS, problems, required=False)
    pct = risk.get("marketplace_min_rating_pct")
    if "marketplace_min_rating_pct" in risk and not (_is_number(pct) and 0 <= pct <= 100):
        problems.append(("risk.marketplace_min_rating_pct", "expected a number from 0 to 100"))
    count = risk.get("marketplace_min_ratings")
    if "marketplace_min_ratings" in risk and not (type(count) is int and count >= 0):
        problems.append(("risk.marketplace_min_ratings", "expected a non-negative integer"))
    depth = risk.get("deep_depth_usd")
    if "deep_depth_usd" in risk and not (_is_number(depth) and depth >= 0):
        problems.append(("risk.deep_depth_usd", "expected a non-negative number"))

    for prefix, item in _objects(data, "accounts", ACCOUNT_FIELDS, problems):
        if not _string(item.get("retailer"), HOSTNAME):
            problems.append((prefix + ".retailer", "required lowercase retailer host, such as example.com"))
        if "session" in item and not _string(item.get("session"), SESSION):
            problems.append((prefix + ".session", "expected <store>:<group>"))
        if not _member(item.get("checkout"), CHECKOUT):
            problems.append((prefix + ".checkout", "required: agent, owner-browser or none"))
        if "identity" in item and not _string(item.get("identity"), KEBAB):
            problems.append((prefix + ".identity", "expected a kebab-case label, never the address"))

    for prefix, item in _objects(data, "home_stores", HOME_STORE_FIELDS, problems):
        if not (_string(item.get("retailer")) and _string(item.get("store"))):
            problems.append((prefix, "expected {retailer, store}"))

    travel = _object(data, "travel", TRAVEL_FIELDS, problems, required=False)
    airports = travel.get("home_airports")
    if "home_airports" in travel and not (isinstance(airports, list)
                                          and all(_string(a, IATA) for a in airports)):
        problems.append(("travel.home_airports", "expected IATA airport codes"))
    if "cabin" in travel and not _member(travel["cabin"], CABINS):
        problems.append(("travel.cabin", "expected economy, premium-economy, business or first"))
    for key in ("checked_bags", "hotel_adults"):
        if key in travel and not (type(travel[key]) is int and travel[key] >= 0):
            problems.append(("travel." + key, "expected a non-negative integer"))
    if "payment_currency" in travel and not _string(travel["payment_currency"], CURRENCY):
        problems.append(("travel.payment_currency", "expected ISO 4217 code"))

    for prefix, item in _objects(data, "forwarders", FORWARDER_FIELDS, problems):
        if not _string(item.get("name"), KEBAB):
            problems.append((prefix + ".name", "required kebab-case name"))
        if "zone" in item and not _string(item.get("zone"), ZONE_ID):
            problems.append((prefix + ".zone", "expected a zone id"))
        if "duty_inclusive" in item and not isinstance(item["duty_inclusive"], bool):
            problems.append((prefix + ".duty_inclusive", "expected Boolean"))
        if "rate_table" in item and not rate_table_ok(item["rate_table"]):
            problems.append((prefix + ".rate_table", "expected a path relative to the config root"))

    prefs = data.get("preferences")
    if "preferences" in data:
        if not isinstance(prefs, dict):
            problems.append(("preferences", "expected an object of category to text"))
        else:
            for key, value in prefs.items():
                where = _join("preferences", key)
                if not _string(key, KEBAB) or len(key) > 40:
                    problems.append((where, "a category is a kebab-case word of at most 40 characters"))
                if not isinstance(value, str):
                    problems.append((where, "expected text"))
                elif DATE_ONLY.fullmatch(value):
                    problems.append((where, "a preference is words, not a date; personal dates never "
                                            "belong in a profile"))
    return problems


def forwarder_table_problems(data, name=None, zone=None, duty_inclusive=None, zip_code=None):
    """Validate a forwarder rate table that a profile's forwarders[].rate_table points at.

    The table has no public source, so it lives privately next to the profile; this is the one
    shape every such table has, so a landed-cost step can read any person's table the same way.
    name, zone and duty_inclusive come from the profile entry and must agree with the table, and
    the zone must be the one the table assigns to the profile's ship-to ZIP.
    """
    if not isinstance(data, dict):
        return [("table", "expected a JSON object")]
    problems = []
    _scan_private(data, "", problems)
    _closed(data, FORWARDER_TABLE_FIELDS, "", problems)
    version = data.get("schema_version")
    if type(version) is not int or version != 1:
        problems.append(("schema_version", "required integer equal to 1"))
    if not _string(data.get("name"), KEBAB) or (name is not None and data.get("name") != name):
        problems.append(("name", "required kebab-case name equal to the profile's forwarders[].name"))
    if not _string(data.get("currency"), CURRENCY):
        problems.append(("currency", "required ISO 4217 code"))
    if not isinstance(data.get("duty_inclusive"), bool):
        problems.append(("duty_inclusive", "required Boolean"))
    elif isinstance(duty_inclusive, bool) and data["duty_inclusive"] != duty_inclusive:
        problems.append(("duty_inclusive", "disagrees with the profile's forwarders[] entry"))
    if not _member(data.get("zone_by"), ZONE_BY):
        problems.append(("zone_by", "required: zip-first-digit"))
    zones = data.get("zones")
    if not (isinstance(zones, dict) and zones and all(
            _string(k, ZONE_ID) and isinstance(v, list) and v and all(_string(x, DIGITS) for x in v)
            for k, v in zones.items())):
        problems.append(("zones", "required object of zone id to postal-code prefixes"))
        zones = {}
    if isinstance(zone, str) and zones and zone not in zones:
        problems.append(("zones", "the profile's zone is not defined in this table"))
    elif isinstance(zone, str) and zones and _string(zip_code) and _member(data.get("zone_by"), ZONE_BY):
        if zip_code[:1] not in zones.get(zone, []):
            problems.append(("zones", "the profile's zone is not the zone of its ship-to ZIP"))
    classes = data.get("classes")
    if not (isinstance(classes, dict) and classes):
        problems.append(("classes", "required object of goods class to per-zone tiers"))
        classes = {}
    for cls, by_zone in classes.items():
        prefix = _join("classes", cls)
        if not _string(cls, KEBAB) or not isinstance(by_zone, dict):
            problems.append((prefix, "expected a kebab-case class mapping zone ids to tiers"))
            continue
        for zone_id, tiers in by_zone.items():
            where = _join(prefix, zone_id)
            if zones and zone_id not in zones:
                problems.append((where, "zone not defined in zones"))
            if not (isinstance(tiers, list) and tiers):
                problems.append((where, "expected a non-empty array of tiers"))
                continue
            for index, tier in enumerate(tiers):
                at = "%s[%d]" % (where, index)
                if not isinstance(tier, dict) or set(tier) - {"min_kg", "max_kg", "rate_per_kg"}:
                    problems.append((at, "expected {min_kg, max_kg, rate_per_kg}"))
                    continue
                low, high, rate = tier.get("min_kg"), tier.get("max_kg"), tier.get("rate_per_kg")
                if not (_is_number(low) and low >= 0):
                    problems.append((at + ".min_kg", "required non-negative number"))
                if high is not None and not (_is_number(high) and _is_number(low) and high >= low):
                    problems.append((at + ".max_kg", "expected null or a number not below min_kg"))
                if not (_is_number(rate) and rate >= 0):
                    problems.append((at + ".rate_per_kg", "required non-negative number"))
    for key in ("volumetric_divisor_cm", "min_billable_kg"):
        if key in data and not (_is_number(data[key]) and data[key] > 0):
            problems.append((key, "expected a positive number"))
    if "notes" in data and not isinstance(data["notes"], str):
        problems.append(("notes", "expected string"))
    if not _string(data.get("source")):
        problems.append(("source", "required: where the table came from"))
    if not valid_date(data.get("verified_date")):
        problems.append(("verified_date", "required date YYYY-MM-DD"))
    return problems


def live_run_problems(row):
    """Validate one live-runs.jsonl row. Returns (severity, field, message) triples.

    A missing or empty required field and a missing gap_reason block; an outcome outside the
    declared set only warns here, because old rows may carry one. The writer refuses both.
    """
    if not isinstance(row, dict):
        return [("block", "row", "expected a JSON object")]
    out = []
    missing = LIVE_RUN_REQUIRED - set(row)
    if missing:
        out.append(("block", ",".join(sorted(missing)), "missing keys"))
    for key in ("domain", "source", "outcome", "detail"):
        if key in row and not _string(row[key]):
            out.append(("block", key, "required non-empty string"))
    if "ts" in row and not valid_timestamp(row["ts"]):
        out.append(("block", "ts", "required ISO-8601 date or date-time"))
    if row.get("user_correction") is not None and not isinstance(row.get("user_correction"), str):
        out.append(("block", "user_correction", "expected null or a string"))
    if _string(row.get("outcome")) and not _member(row.get("outcome"), OUTCOMES):
        out.append(("warn", "outcome", "not in the declared set"))
    if row.get("outcome") == "coverage_gap" and not _member(row.get("gap_reason"), GAP_REASONS):
        out.append(("block", "gap_reason", "requires a valid gap_reason for coverage_gap "
                                           "(CONSTITUTION II.8)"))
    return out


def purchase_problems(row):
    """Validate one purchases.jsonl row. Returns (field, message) pairs."""
    if not isinstance(row, dict):
        return [("row", "expected a JSON object")]
    out = []
    for key in sorted(PURCHASE_REQUIRED - set(row)):
        out.append((key, "required"))
    _closed(row, PURCHASE_FIELDS, "", out)
    if "ts" in row and not valid_timestamp(row["ts"]):
        out.append(("ts", "required ISO-8601 date or date-time"))
    if "profile_id" in row and not _string(row["profile_id"], KEBAB):
        out.append(("profile_id", "required kebab-case id"))
    for key in ("retailer", "order_ref", "item"):
        if key in row and not _string(row[key]):
            out.append((key, "required non-empty string"))
    if "variant_key" in row and not _string(row["variant_key"]):
        out.append(("variant_key", "expected non-empty string"))
    if "notes" in row and not isinstance(row["notes"], str):
        out.append(("notes", "expected string"))
    if "path" in row and not _member(row["path"], PURCHASE_PATHS):
        out.append(("path", "expected one-time, subscription or multi-pack"))
    if "status" in row and not _member(row["status"], PURCHASE_STATUS):
        out.append(("status", "expected placed, cancelled, replaced or returned"))
    if "quantity" in row and not (type(row["quantity"]) is int and row["quantity"] >= 1):
        out.append(("quantity", "expected a positive integer"))
    for key in ("items_total", "tax", "charged_total"):
        if key in row and not (_is_number(row[key]) and row[key] >= 0):
            out.append((key, "expected a non-negative number"))
    if "paid_with" in row and not _member(row["paid_with"], PAID_WITH):
        out.append(("paid_with", "expected store-credit, card, mixed or other"))
    discounts = row.get("discounts", [])
    if not isinstance(discounts, list):
        out.append(("discounts", "expected array"))
        discounts = []
    for index, item in enumerate(discounts):
        prefix = "discounts[%d]" % index
        if not isinstance(item, dict):
            out.append((prefix, "expected object"))
            continue
        _closed(item, {"type", "amount", "mark"}, prefix, out)
        if not _string(item.get("type")):
            out.append((prefix + ".type", "required"))
        if not (_is_number(item.get("amount")) and item["amount"] >= 0):
            out.append((prefix + ".amount", "required non-negative number"))
        if not _member(item.get("mark"), DISCOUNT_MARKS):
            out.append((prefix + ".mark", "expected cart_tested, unverified, expired_failed or paid_later"))
    sub = row.get("subscription")
    if row.get("path") == "subscription":
        if not isinstance(sub, dict):
            out.append(("subscription", "required for a subscription purchase"))
        else:
            _closed(sub, {"interval", "next_delivery"}, "subscription", out)
            if not _string(sub.get("interval"), INTERVAL):
                out.append(("subscription.interval", "expected an interval such as 6-weeks or 2-months"))
            if row.get("status") == "placed" or sub.get("next_delivery") is not None:
                if not valid_date(sub.get("next_delivery")):
                    out.append(("subscription.next_delivery", "required date YYYY-MM-DD while it is placed"))
    elif sub is not None:
        out.append(("subscription", "only a subscription purchase carries subscription terms"))
    if row.get("status") == "replaced":
        if not _string(row.get("replaced_by")) or row.get("replaced_by") == row.get("order_ref"):
            out.append(("replaced_by", "required, and different from order_ref, when status is replaced"))
    elif "replaced_by" in row:
        out.append(("replaced_by", "only a replaced order names its replacement"))
    return out
