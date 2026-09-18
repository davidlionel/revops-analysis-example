"""
Generates a synthetic HubSpot deals extract with deliberately planted
pipeline pathologies for portfolio analysis.

Output shape mirrors what a HubSpot -> Postgres sync would produce for the
deals object, including per-stage entry timestamps.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(20260908)

# HubSpot default sales pipeline, in order
STAGES = [
    "appointmentscheduled",
    "qualifiedtobuy",
    "presentationscheduled",
    "decisionmakerboughtin",
    "contractsent",
]
CLOSED = ["closedwon", "closedlost"]

STAGE_LABELS = {
    "appointmentscheduled": "Appointment Scheduled",
    "qualifiedtobuy": "Qualified To Buy",
    "presentationscheduled": "Presentation Scheduled",
    "decisionmakerboughtin": "Decision Maker Bought-In",
    "contractsent": "Contract Sent",
    "closedwon": "Closed Won",
    "closedlost": "Closed Lost",
}

OWNERS = [
    "Dana Whitfield",
    "Marcus Oyelaran",
    "Priya Raghunathan",
    "Tom Bergstrom",
    "Alicia Ferreira",
    "Kenji Watanabe",
]

SOURCES = [
    "Inbound - Demo Request",
    "Inbound - Content",
    "Inbound - Partner Referral",
    "Outbound - SDR",
    "Outbound - Founder",
    "Event",
]

DEAL_TYPES = ["New Business", "Expansion", "Renewal"]

COMPANIES = [
    "Northwind Logistics", "Arclight Systems", "Ferrous Labs", "Brightpath Health",
    "Cascade Analytics", "Meridian Freight", "Quillon Software", "Tessellate",
    "Harborview Media", "Ridgeline Robotics", "Solvent Bio", "Anvil Retail",
    "Copperline Energy", "Dovetail HR", "Ember Financial", "Foxglove Design",
    "Granite Peak Insurance", "Halcyon Devices", "Ironwood Capital", "Juniper Cloud",
    "Kestrel Manufacturing", "Lumen Diagnostics", "Marlowe Legal", "Nimbus Storage",
    "Oakhurst Foods", "Pinnacle Staffing", "Quarry Digital", "Redwood Telecom",
    "Saltmarsh Marine", "Thornbury Group", "Umbra Security", "Vantage Point Realty",
    "Westfall Automotive", "Xylem Networks", "Yarrow Nutrition", "Zephyr Aviation",
    "Alder Creek Brewing", "Blackstone Tooling", "Cinder Interactive", "Dunmore Textiles",
]

START = datetime(2025, 1, 6)
TODAY = datetime(2026, 9, 8)


def biz_amount(deal_type):
    base = {
        "New Business": (8000, 145000),
        "Expansion": (4000, 60000),
        "Renewal": (12000, 180000),
    }[deal_type]
    raw = random.uniform(*base)
    # cluster on round-ish numbers the way real quotes do
    return round(raw / 250) * 250


def make_deal(idx, profile):
    """profile drives which pathology (if any) the deal exhibits."""
    company = random.choice(COMPANIES)
    deal_type = random.choices(DEAL_TYPES, weights=[0.62, 0.24, 0.14])[0]
    owner = profile.get("owner") or random.choice(OWNERS)
    source = profile.get("source") or random.choices(
        SOURCES, weights=[0.22, 0.18, 0.12, 0.26, 0.10, 0.12]
    )[0]

    created = START + timedelta(
        days=random.randint(0, (TODAY - START).days - 20),
        hours=random.randint(8, 18),
        minutes=random.choice([0, 15, 30, 45]),
    )

    path = profile["path"]          # list of stages actually entered
    outcome = profile["outcome"]    # 'closedwon' | 'closedlost' | None (open)
    pace = profile.get("pace", "normal")

    entries = {}
    cursor = created

    for i, stage in enumerate(path):
        if i == 0:
            gap_h = 0
        elif pace == "sameday":
            gap_h = random.randint(1, 6)
        elif pace == "slow":
            gap_h = random.randint(24 * 14, 24 * 55)
        else:
            gap_h = random.randint(24 * 2, 24 * 21)
        cursor = cursor + timedelta(hours=gap_h)
        entries[stage] = cursor

    close_stage_ts = None
    if outcome:
        if pace == "sameday":
            gap_h = random.randint(1, 5)
        elif pace == "slow":
            gap_h = random.randint(24 * 20, 24 * 70)
        else:
            gap_h = random.randint(24 * 3, 24 * 30)
        close_stage_ts = cursor + timedelta(hours=gap_h)
        entries[outcome] = close_stage_ts

    # keep every stage entry in the past; overrunning timelines slide back
    if entries:
        overrun = max(entries.values()) - TODAY
        if overrun.total_seconds() > 0:
            shift = overrun + timedelta(days=random.randint(2, 45))
            created = created - shift
            entries = {k: v - shift for k, v in entries.items()}
            cursor = cursor - shift
            if close_stage_ts:
                close_stage_ts = close_stage_ts - shift

    # ---- planted corruptions -------------------------------------------
    if profile.get("backdate"):
        # one stage entry lands before the deal was created
        victim = random.choice(path)
        entries[victim] = created - timedelta(days=random.randint(3, 40))

    if profile.get("out_of_order") and len(path) >= 3:
        a, b = sorted(random.sample(range(1, len(path)), 2))
        sa, sb = path[a], path[b]
        entries[sa], entries[sb] = entries[sb], entries[sa]
    # --------------------------------------------------------------------

    if outcome:
        current = outcome
        last_ts = max(entries.values())
        close_date = last_ts
    else:
        current = path[-1]
        last_ts = max(entries.values())
        if profile.get("stale_closedate"):
            close_date = TODAY - timedelta(days=random.randint(20, 190))
        else:
            close_date = TODAY + timedelta(days=random.randint(5, 120))

    amount = biz_amount(deal_type)
    if profile.get("no_amount"):
        amount = random.choice(["", "0"])

    row = {
        "deal_id": str(6100000000 + idx * 7 + random.randint(0, 3)),
        "dealname": f"{company} - {deal_type}",
        "amount": amount,
        "dealstage": current,
        "dealstage_label": STAGE_LABELS[current],
        "pipeline": "default",
        "dealtype": deal_type,
        "deal_source": source,
        "hubspot_owner": owner,
        "createdate": created.strftime("%Y-%m-%d %H:%M:%S"),
        "closedate": close_date.strftime("%Y-%m-%d %H:%M:%S"),
        "hs_is_closed": "true" if outcome else "false",
        "hs_is_closed_won": "true" if outcome == "closedwon" else "false",
    }

    for s in STAGES + CLOSED:
        key = f"hs_date_entered_{s}"
        row[key] = entries[s].strftime("%Y-%m-%d %H:%M:%S") if s in entries else ""

    row["hs_lastmodifieddate"] = max(
        max(entries.values()), created
    ).strftime("%Y-%m-%d %H:%M:%S")

    return row


def full_path():
    return list(STAGES)


def build():
    profiles = []

    # ---------------------------------------------------------------
    # 1. Clean full-path deals. Low win rate.
    # ---------------------------------------------------------------
    for _ in range(196):
        r = random.random()
        if r < 0.11:
            outcome = "closedwon"
        elif r < 0.75:
            outcome = "closedlost"
        else:
            outcome = None
        depth = len(STAGES) if outcome else random.randint(1, len(STAGES))
        profiles.append({"path": full_path()[:depth], "outcome": outcome})

    # ---------------------------------------------------------------
    # 2. Skipped qualification. High win rate. Concentrated in partner
    #    referral + two owners. This is the headline pathology, and the
    #    concentration is what makes it ambiguous rather than obvious.
    # ---------------------------------------------------------------
    for _ in range(88):
        path = [s for s in STAGES if s != "qualifiedtobuy"]
        depth = random.randint(2, len(path))
        r = random.random()
        if r < 0.32:
            outcome = "closedwon"
        elif r < 0.80:
            outcome = "closedlost"
        else:
            outcome = None
        prof = {"path": path[:depth] if not outcome else path, "outcome": outcome}
        if random.random() < 0.55:
            prof["source"] = "Inbound - Partner Referral"
        if random.random() < 0.5:
            prof["owner"] = random.choice(["Dana Whitfield", "Kenji Watanabe"])
        profiles.append(prof)

    # ---------------------------------------------------------------
    # 3. Created directly into a late stage. Never touched early pipeline.
    # ---------------------------------------------------------------
    for _ in range(34):
        start_at = random.choice([2, 3, 4])
        path = STAGES[start_at:]
        outcome = random.choices(["closedwon", "closedlost", None], weights=[0.40, 0.42, 0.18])[0]
        profiles.append({"path": path, "outcome": outcome})

    # ---------------------------------------------------------------
    # 4. Same-day rubber-stamp traversal.
    # ---------------------------------------------------------------
    for _ in range(17):
        profiles.append({
            "path": full_path(),
            "outcome": random.choices(["closedwon", "closedlost"], weights=[0.35, 0.65])[0],
            "pace": "sameday",
        })

    # ---------------------------------------------------------------
    # 5. Zombies. Open, slow, stale close dates.
    # ---------------------------------------------------------------
    for _ in range(24):
        depth = random.randint(2, 4)
        profiles.append({
            "path": full_path()[:depth],
            "outcome": None,
            "pace": "slow",
            "stale_closedate": random.random() < 0.75,
        })

    # ---------------------------------------------------------------
    # 6. Timestamp corruption: backdated entries and out-of-order stages.
    # ---------------------------------------------------------------
    for _ in range(13):
        profiles.append({
            "path": full_path(),
            "outcome": random.choices(["closedwon", "closedlost"], weights=[0.35, 0.65])[0],
            "backdate": True,
        })

    for _ in range(9):
        profiles.append({
            "path": full_path(),
            "outcome": random.choice(["closedwon", "closedlost", None]),
            "out_of_order": True,
        })

    # ---------------------------------------------------------------
    # 7. Closed-won with no amount.
    # ---------------------------------------------------------------
    for _ in range(8):
        profiles.append({
            "path": [s for s in STAGES if s != "qualifiedtobuy"],
            "outcome": "closedwon",
            "no_amount": True,
        })

    random.shuffle(profiles)
    return [make_deal(i, p) for i, p in enumerate(profiles)]


rows = build()

cols = [
    "deal_id", "dealname", "amount", "dealstage", "dealstage_label", "pipeline",
    "dealtype", "deal_source", "hubspot_owner", "createdate", "closedate",
    "hs_is_closed", "hs_is_closed_won",
] + [f"hs_date_entered_{s}" for s in STAGES + CLOSED] + ["hs_lastmodifieddate"]

with open("/home/claude/deals_extract.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

# HubSpot-importable subset: stage-history properties are system-set and
# cannot be imported, so they are excluded here.
import_cols = [
    "dealname", "amount", "dealstage_label", "pipeline", "dealtype",
    "deal_source", "closedate",
]
with open("/home/claude/deals_hubspot_import.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=import_cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        rr = dict(r)
        if rr["amount"] == "":
            rr["amount"] = ""
        w.writerow(rr)

print(f"rows: {len(rows)}")
