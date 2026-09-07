"""Business-case arithmetic for requirements/08-business-case.md.

Run:  uv run scripts/business_case.py            print the generated tables
      uv run scripts/business_case.py --write    insert them between the markers in requirements/08
      uv run scripts/business_case.py --check    verify 08, 06 and README against the model
                                                 (called by scripts/lint_docs.py)
      uv run scripts/business_case.py --self-test

Every derived number in requirements/08 comes from the ASSUMPTIONS block below.
Season 1 replaces the assumptions with measured values (requirements/08 §0);
edit the block, run --write, and the tables in 08 follow. Stdlib only.

Model in one paragraph. Ladder values are end-of-year run rates (visitor-days per
day); yearly volume is the mean of adjacent run rates × open days. The weekday /
weekend ratio r gives the weekend-day average W = 7D / (5r + 2) and the peak day
W × s. Repeat share p of households evolves as a stock: p_y = p_{y-1} × retention
+ (1 - p_{y-1}) × (organic + flywheel), flywheel = adoption × opt-in × nudge reach ×
return. Every repeat visit is priced as a pass visit (lower bound on revenue).
Payback is platform payback only, undiscounted: cost = CAPEX + OPEX(V); benefit =
savings from Phase 2 plus incremental visitor-days credited to the platform from
Phase 3 at pass contribution, minus the re-pricing of converted single visits.
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC_08 = ROOT / "requirements/08-business-case.md"
DOC_06 = ROOT / "requirements/06-suggested-okrs.md"
README = ROOT / "README.md"

YEARS = ("Y0 (today)", "Y1", "Y2", "Y3 (target)")


# --------------------------------------------------------------------------- assumptions
@dataclass(frozen=True)
class Assumptions:
    # Estate and calendar
    open_days: int = 300
    party_size: float = 3.5            # persons per household visit (A9)
    repeat_visits: int = 3             # k — visits per year by a repeating household

    # Attendance ladder: end-of-year run rates (daily average visitor-days), Y0..Y3
    run_rate: tuple = (5_000, 6_500, 9_500, 15_000)
    ratio: tuple = (0.35, 0.38, 0.45, 0.60)   # weekday / weekend-day ratio r (OKR 1.5)
    peak_factor: float = 1.4           # peak day = W × s (A14)
    peak_hour_share: float = 0.20      # share of a day's arrivals in the peak hour (A14)
    on_site_share: float = 0.55        # share of the day's visitor-days on site at 14:00 (A14)

    # Flywheel funnel (requirements/08 §3), Y1..Y3. Y0 has none of it.
    organic_repeat: float = 0.10       # p today (OKR 1.2 current estimate)
    habit_retention_today: float = 0.50  # share of today's repeaters who repeat again next year
    adoption: tuple = (0.25, 0.45, 0.60)      # households creating an itinerary
    opt_in: tuple = (0.40, 0.55, 0.75)        # of those, opening an account
    nudge_reach: tuple = (0.30, 0.50, 0.90)   # of those, reached by an opened nudge (plain offer mail before Phase 3)
    return_rate: tuple = (0.40, 0.50, 0.70)   # of those, back within 12 months
    pass_conversion: tuple = (0.50, 0.60, 0.70)  # of returners, holding a pass (measured; not in the revenue model)
    renewal: tuple = (0.60, 0.65, 0.70)       # of last year's repeaters, repeating again (pass renewal / habit)

    # Revenue per visitor-day, gross (requirements/08 §0)
    admission_single: float = 15.0
    admission_pass: float = 9.0        # season pass at 1.8 single admissions per person, used k = 3 times
    on_site: float = 6.0
    cogs_share: float = 0.50           # A15 — cost of goods on on-site sales
    variable_ops: float = 1.0          # A15 — per visitor-day
    ticketing_fee: float = 0.15        # A15 — per credential
    credentials_per_visitor_day: float = 1.0  # conservative: one per person-admission, as in requirements/04

    # Platform cost (requirements/04 cost model)
    capex: float = 310_000
    depreciation_years: int = 5
    opex_fixed: float = 580_000        # team, cellular, maintenance, base cloud and LLM
    opex_per_visitor_day: float = 0.165  # ticketing fee 0.15 + cloud and LLM scaling 0.015

    # Savings (contribution), from Phase 2 (OKR 3.2 and 2.4 targets)
    vet_cost: float = 300_000
    vet_saving: tuple = (0.15, 0.30)   # at 12 / 36 months
    field_payroll: float = 1_200_000
    idle_share: float = 0.15
    idle_saving: tuple = (0.30, 0.50)  # at 12 / 36 months
    savings_start_month: int = 18

    # Attribution (requirements/08 §4)
    attribution_start_month: int = 30  # Phase 3 levers live
    conversion_share: float = 0.5      # share of incremental visits that come via converting a single-visit household
    incremental_rows: tuple = (200_000, 400_000, 600_000)  # incremental visitor-days per year credited to the platform
    horizon_months: int = 120

    # Capacity (site figures → A14; replaced by the site survey)
    parking_spaces: int = 2_500
    parking_turns: float = 1.5
    persons_per_car: float = 3.2
    car_share: float = 0.80
    fnb_seats: int = 1_500
    fnb_turns: int = 4                 # 11:30–14:30
    lunch_on_site_share: float = 0.55  # share of the day's visitor-days on site at lunch
    seated_lunch_uptake: float = 0.55  # of those, taking a seated lunch
    gate_lanes: int = 6
    scans_per_lane_hour: int = 900
    rides: int = 40
    riders_per_hour: tuple = (150, 300)
    ride_hours: int = 8
    m2_per_person: float = 3.3         # Fruin LOS C


A = Assumptions()


# --------------------------------------------------------------------------- formatting
def n(x: float) -> str:
    return f"{round(x):,}"


def pct(x: float, digits: int = 0) -> str:
    return f"{x * 100:.{digits}f}%"


def eur(x: float) -> str:
    if abs(x) >= 1_000_000:
        return f"€{x / 1_000_000:.2f}M".replace(".00M", "M")
    if abs(x) >= 1_000:
        return f"€{x / 1_000:.0f}k"
    return f"€{x:.2f}"


def eur_m(x: float) -> str:
    return f"€{x / 1_000_000:.1f}M"


def ratio_str(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".") if x != round(x) else f"{x:.1f}"


# --------------------------------------------------------------------------- model
def weekend_day(D: float, r: float, a: Assumptions = A) -> float:
    """Weekend-day average W from the daily average D: weekly = W(5r + 2) = 7D."""
    return 7 * D / (5 * r + 2)


def opex(V: float, a: Assumptions = A) -> float:
    return a.opex_fixed + a.opex_per_visitor_day * V


def contribution(a: Assumptions = A) -> tuple[float, float]:
    """Contribution per visitor-day: (single visit, pass visit)."""
    variable = a.ticketing_fee * a.credentials_per_visitor_day + a.variable_ops + a.cogs_share * a.on_site
    single = a.admission_single + a.on_site - variable
    pass_ = a.admission_pass + a.on_site - variable
    return single, pass_


def organic_conversion(a: Assumptions = A) -> float:
    """Steady state today: p0 = p0 × retention + (1 - p0) × g  →  g."""
    return a.organic_repeat * (1 - a.habit_retention_today) / (1 - a.organic_repeat)


def repeat_share(a: Assumptions = A) -> list[float]:
    """p per year (Y0..Y3) from the funnel, as a stock."""
    g = organic_conversion(a)
    p = [a.organic_repeat]
    for y in range(3):
        fly = a.adoption[y] * a.opt_in[y] * a.nudge_reach[y] * a.return_rate[y]
        p.append(p[-1] * a.renewal[y] + (1 - p[-1]) * min(1.0, g + fly))
    return p


def yearly_volume(a: Assumptions = A) -> list[float]:
    """Visitor-days per year: Y0 at today's run rate; Y1..Y3 = mean of adjacent run rates × open days."""
    rr = a.run_rate
    return [rr[0] * a.open_days] + [(rr[y - 1] + rr[y]) / 2 * a.open_days for y in range(1, 4)]


@dataclass
class YearRow:
    label: str
    D: float
    r: float
    W: float
    weekday: float
    peak: float
    peak_hour: float
    on_site: float
    V: float
    p: float
    households: float
    repeat_vd: float
    single_vd: float
    repeat_households: float
    gross: float
    contribution: float

    @property
    def visit_share_repeat(self) -> float:
        return self.repeat_vd / self.V

    @property
    def revenue_per_vd(self) -> float:
        return self.gross / self.V

    @property
    def revenue_per_household(self) -> float:
        return self.gross / self.households


def ladder(a: Assumptions = A) -> list[YearRow]:
    rows = []
    ps = repeat_share(a)
    Vs = yearly_volume(a)
    c_single, c_pass = contribution(a)
    k = a.repeat_visits
    for y in range(4):
        D, r, p, V = a.run_rate[y], a.ratio[y], ps[y], Vs[y]
        W = weekend_day(D, r, a)
        peak = W * a.peak_factor
        hv = V / a.party_size                       # household visits
        H = hv / (p * k + 1 - p)                    # unique households
        repeat_hv = H * p * k
        single_hv = H * (1 - p)
        repeat_vd, single_vd = repeat_hv * a.party_size, single_hv * a.party_size
        gross = single_vd * (a.admission_single + a.on_site) + repeat_vd * (a.admission_pass + a.on_site)
        contrib = single_vd * c_single + repeat_vd * c_pass
        rows.append(YearRow(YEARS[y], D, r, W, W * r, peak, peak * a.peak_hour_share, peak * a.on_site_share,
                            V, p, H, repeat_vd, single_vd, H * p, gross, contrib))
    return rows


# --------------------------------------------------------------------------- capacity
@dataclass
class Constraint:
    name: str
    assumption: str
    arithmetic: str
    holds_until: float | None      # peak-day visitor-days; None = not a hard limit
    verdict: str

    def binds_year(self, rows: list[YearRow]) -> str:
        if self.holds_until is None:
            return "—"
        for row in rows[1:]:
            if row.peak > self.holds_until:
                return f"**{row.label.split()[0]}** (peak ≈ {n(row.peak)})"
        return "beyond Y3"


def capacity(a: Assumptions = A) -> list[Constraint]:
    parking_persons = a.parking_spaces * a.parking_turns * a.persons_per_car
    parking = parking_persons / a.car_share
    meals = a.fnb_seats * a.fnb_turns
    fnb = meals / (a.lunch_on_site_share * a.seated_lunch_uptake)
    fnb_strict = meals / a.seated_lunch_uptake
    gates_hour = a.gate_lanes * a.scans_per_lane_hour
    gates = gates_hour / a.peak_hour_share
    y3 = ladder(a)[3]
    rides_lo = a.rides * a.riders_per_hour[0] * a.ride_hours
    rides_hi = a.rides * a.riders_per_hour[1] * a.ride_hours
    area_ha = y3.on_site * a.m2_per_person / 10_000
    return [
        Constraint(
            "Parking",
            f"{n(a.parking_spaces)} spaces, {a.parking_turns} turns/day, {a.persons_per_car} per car, "
            f"{pct(a.car_share)} arrive by car (→ site survey, car counters)",
            f"{n(a.parking_spaces)} × {a.parking_turns} × {a.persons_per_car} ÷ {a.car_share} = **{n(parking)}**",
            parking,
            f"Binds first. Target peak ≈ {n(y3.peak)} needs ≈ ×{y3.peak / parking:.0f} spaces or a car share "
            f"≤ {pct(parking_persons / y3.peak)}: park-and-ride / coach share, or fewer peak arrivals via "
            f"timed entry (FR-1.7) and quiet-day shaping (S5)",
        ),
        Constraint(
            "F&B seating at lunch",
            f"{n(a.fnb_seats)} seats × {a.fnb_turns} turns 11:30–14:30 = {n(meals)} meals; "
            f"{pct(a.lunch_on_site_share)} of the day's visitor-days on site at lunch × "
            f"{pct(a.seated_lunch_uptake)} of those take a seated lunch (→ `PurchaseRecorded`, queue counters)",
            f"{n(meals)} ÷ ({a.lunch_on_site_share} × {a.seated_lunch_uptake}) = **{n(fnb)}**. "
            f"If the {pct(a.seated_lunch_uptake)} uptake applied to *all* visitor-days, capacity would be "
            f"{n(fnb_strict)} — F&B would bind today; the two rates are measured separately in season 1",
            fnb,
            "Binds. Companion steers lunch times and under-used outlets (S4); spend per zone shows where",
        ),
        Constraint(
            "Gates",
            f"{a.gate_lanes} lanes × {n(a.scans_per_lane_hour)} scans/h, one scan per person (a pass admitting "
            f"{a.party_size} people on one scan makes this conservative by up to ×{a.party_size}); "
            f"{pct(a.peak_hour_share)} of arrivals in the peak hour (→ `GateEntered.persons_admitted`)",
            f"{n(gates_hour)}/h ÷ {a.peak_hour_share} = **{n(gates)}**",
            gates,
            f"Marginal: peak hour ≈ {n(y3.peak_hour)} scans/h against {n(gates_hour)}; holds only with "
            f"timed-entry slots spreading arrivals (FR-1.7), or two more lanes",
        ),
        Constraint(
            "Rides",
            f"{a.rides} historic rides × {a.riders_per_hour[0]}–{a.riders_per_hour[1]} riders/h × {a.ride_hours} h "
            f"= {n(rides_lo / 1000)}k–{n(rides_hi / 1000)}k rides/day (→ ride cycle counters)",
            f"{rides_lo / y3.peak:.1f}–{rides_hi / y3.peak:.1f} rides per visitor on the target peak day",
            None,
            "Not a hard limit but the experience constraint: OKR 2.2 (p90 queue ≤ 20 min) breaks first; "
            "S3/S4 load spreading is the lever",
        ),
        Constraint(
            "Paths and lawns",
            f"{a.m2_per_person} m² per person (Fruin LOS C) for {n(y3.on_site)} on site at 14:00 "
            f"(→ site plan, zone counters)",
            f"{n(y3.on_site)} × {a.m2_per_person} m² ≈ **{area_ha:.1f} ha** of walkable public area",
            None,
            "Holds if the estate's public circulation area is at least that (site plan); below it, "
            "zone caps decided by ops from live occupancy (S3 read models)",
        ),
        Constraint(
            "Estate systems",
            "broker cluster, LoRaWAN, ingestion sized in hld/core for > 100k visitor-days",
            f"peak-hour gate rate ≈ {y3.peak_hour / 3600:.1f} scans/s",
            None,
            "Hold ([capacity table](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class))",
        ),
    ]


# --------------------------------------------------------------------------- payback
def savings_rate(month: int, a: Assumptions = A) -> float:
    """Annual savings rate at a given month: ramps from the 12-month to the 36-month OKR targets."""
    if month < a.savings_start_month:
        return 0.0
    s12 = a.vet_cost * a.vet_saving[0] + a.field_payroll * a.idle_share * a.idle_saving[0]
    s36 = a.vet_cost * a.vet_saving[1] + a.field_payroll * a.idle_share * a.idle_saving[1]
    t = min(1.0, (month - a.savings_start_month) / (36 - a.savings_start_month))
    return s12 + (s36 - s12) * t


def net_per_incremental_vd(a: Assumptions = A) -> float:
    """Pass contribution minus the re-pricing of a converted single visit, spread over its k - 1 new visits."""
    c_single, c_pass = contribution(a)
    debit = (c_single - c_pass) / (a.repeat_visits - 1)
    return c_pass - a.conversion_share * debit


def simulate(incremental_vd: float, a: Assumptions = A) -> tuple[int | None, float, float]:
    """Return (break-even month or None, cumulative cost at 36, cumulative benefit at 36)."""
    Vs = yearly_volume(a)
    run_rate_V = a.run_rate[3] * a.open_days
    cost = a.capex
    benefit = 0.0
    be = None
    cost36 = benefit36 = 0.0
    net = net_per_incremental_vd(a)
    for m in range(1, a.horizon_months + 1):
        V = Vs[min(3, (m - 1) // 12 + 1)] if m <= 36 else run_rate_V
        cost += opex(V, a) / 12
        benefit += savings_rate(m, a) / 12
        if m > a.attribution_start_month:
            benefit += incremental_vd * net / 12
        if be is None and benefit >= cost:
            be = m
        if m == 36:
            cost36, benefit36 = cost, benefit
    return be, cost36, benefit36


def payback_window(a: Assumptions = A) -> tuple[int, int] | None:
    """(earliest, latest) break-even year over the sensitivity rows that do break even."""
    months = [simulate(x, a)[0] for x in a.incremental_rows]
    months = [m for m in months if m is not None]
    if not months:
        return None
    return math.ceil(min(months) / 12), math.ceil(max(months) / 12)


def break_even_today(a: Assumptions = A) -> dict[str, float]:
    V0 = yearly_volume(a)[0]
    annual_cost = opex(V0, a) + a.capex / a.depreciation_years
    c_single, c_pass = contribution(a)
    return {
        "annual_cost": annual_cost,
        "vd_pass": annual_cost / c_pass,
        "vd_single": annual_cost / c_single,
        "on_site_sales": annual_cost / (1 - a.cogs_share),
        "on_site_today": V0 * a.on_site,
    }


# --------------------------------------------------------------------------- tables
def table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def t_run_rate(a: Assumptions = A) -> str:
    rows = ladder(a)
    caps = capacity(a)
    binds = []
    for row in rows:
        b = [c.name.lower() for c in caps if c.holds_until is not None and row.peak > c.holds_until]
        binds.append(", ".join(b) if b else "none")
    return table(
        ["End-of-year run rate", *[r.label for r in rows]],
        [
            ["Daily average D (visitor-days)", *[n(r.D) for r in rows]],
            ["Growth vs. previous year", "—", *[f"+{pct(rows[y].D / rows[y - 1].D - 1)}" for y in range(1, 4)]],
            ["Weekday / weekend ratio r (OKR 1.5)", *[ratio_str(r.r) for r in rows]],
            ["Weekend-day average W = 7D ÷ (5r + 2)", *[n(r.W) for r in rows]],
            ["Weekday average W × r", *[n(r.weekday) for r in rows]],
            [f"Peak day W × {a.peak_factor}", *[n(r.peak) for r in rows]],
            [f"Peak-hour arrivals ({pct(a.peak_hour_share)} of the peak day)", *[n(r.peak_hour) for r in rows]],
            [f"On site at 14:00 ({pct(a.on_site_share)} of the peak day)", *[n(r.on_site) for r in rows]],
            ["Constraints exceeded on the peak day (§1)", *binds],
        ],
    )


def t_volume(a: Assumptions = A) -> str:
    rows = ladder(a)
    base = rows[0]
    return table(
        ["Over the year", *[r.label for r in rows]],
        [
            ["Visitor-days (mean of adjacent run rates × 300 open days)", *[eur_m(r.V).replace("€", "") for r in rows]],
            ["Repeat share of households p (OKR 1.2) — from the funnel in §3", *[pct(r.p) for r in rows]],
            [f"Unique households (visitor-days ÷ {a.party_size} ÷ (pk + 1 − p), k = {a.repeat_visits})",
             *[f"{r.households / 1000:.0f}k" for r in rows]],
            ["Repeat households", *[f"{r.repeat_households / 1000:.0f}k" for r in rows]],
            ["Repeat visitor-days — share of all visits", *[f"{eur_m(r.repeat_vd).replace('€', '')} — {pct(r.visit_share_repeat)}" for r in rows]],
            ["Single visitor-days", *[eur_m(r.single_vd).replace("€", "") for r in rows]],
            ["Passes' share of admissions under the lower-bound assumption (OKR 1.3 model)", *[pct(r.visit_share_repeat) for r in rows]],
            [f"Gross revenue (single visit {eur(a.admission_single + a.on_site)}, pass visit {eur(a.admission_pass + a.on_site)})",
             *[eur_m(r.gross) for r in rows]],
            ["Revenue per visitor-day", *[f"€{r.revenue_per_vd:.1f}" for r in rows]],
            ["Revenue per household per year (OKR 1.4 model)",
             *[f"€{r.revenue_per_household:.0f}" + ("" if r is base else f" ({'+' if r.revenue_per_household >= base.revenue_per_household else ''}{pct(r.revenue_per_household / base.revenue_per_household - 1)})") for r in rows]],
            [f"Contribution (single {eur(contribution(a)[0])}, pass {eur(contribution(a)[1])} per visitor-day)",
             *[eur_m(r.contribution) for r in rows]],
        ],
    )


def t_capacity(a: Assumptions = A) -> str:
    rows = ladder(a)
    return table(
        ["Constraint", "Assumption (→ measured by)", "Holds until (peak-day visitor-days)", "First ladder year it binds", "Verdict and lever"],
        [[c.name, c.assumption, c.arithmetic, c.binds_year(rows), c.verdict] for c in capacity(a)],
    )


def t_funnel(a: Assumptions = A) -> str:
    ps = repeat_share(a)
    g = organic_conversion(a)
    fly = [a.adoption[y] * a.opt_in[y] * a.nudge_reach[y] * a.return_rate[y] for y in range(3)]
    stages = [
        ("Companion adoption", "households that create an itinerary", a.adoption, "`ItineraryCreated` ÷ households admitted", "S4 FAQ (Phase 1) → day planning (Phase 2)"),
        ("Opt-in", "of those, households opening an account", a.opt_in, "account opt-in (FR-1.6) ÷ companion households", "the companion gives a reason to keep an account"),
        ("Nudge reach", "of those, reached by a nudge they opened", a.nudge_reach, "`NudgeSent` with an open ÷ accounts", "plain offer mail from the ticketing platform before Phase 3; S4 personalised nudges from month 30"),
        ("Return", "of those, back within 12 months", a.return_rate, "`GateEntered` of the household after a nudge", "quiet-day offer and season-pass offer in the nudge"),
        ("Pass conversion", "of returners, holding a season pass", a.pass_conversion, "pass `TicketPurchased` or upgrade credit ÷ returning households", "measured for OKR 1.3; the revenue model prices every repeat visit as a pass visit regardless (lower bound)"),
        ("Renewal / habit retention", "of last year's repeat households, repeating again", a.renewal, "`PassRenewed`; repeat `GateEntered` across years for accounts", "OKR 1.6; pass renewal executed by the ticketing platform"),
    ]
    rows = [[name, what, *[pct(v[y]) for y in range(3)], event, ramp] for name, what, v, event, ramp in stages]
    rows.append(["**Flywheel conversion** (adoption × opt-in × reach × return)", "share of non-repeating households converted this year", *[pct(f, 1) for f in fly], "derived", ""])
    rows.append([f"**Organic conversion**", f"today's steady state: p = {pct(a.organic_repeat)} with retention {pct(a.habit_retention_today)}", *[pct(g, 1)] * 3, "exit survey (A14)", "constant"])
    rows.append(["**Repeat share p** = p₋₁ × retention + (1 − p₋₁) × (organic + flywheel)", f"Y0 = {pct(ps[0])}", *[f"**{pct(ps[y])}**" for y in range(1, 4)], "OKR 1.2", "if p falls short, the ladder's unique-household row grows, not the rates"])
    return table(["Rate", "Meaning", "Y1", "Y2", "Y3 (steady state)", "Measured by", "Why it ramps"], rows)


def t_payback(a: Assumptions = A) -> str:
    Vs = yearly_volume(a)
    rr_V = a.run_rate[3] * a.open_days
    c_single, c_pass = contribution(a)
    s18 = savings_rate(a.savings_start_month, a)
    s36 = savings_rate(36, a)
    be = break_even_today(a)
    cum36 = a.capex + sum(opex(Vs[y], a) for y in range(1, 4))
    rows = [
        ["CAPEX (requirements/04), all in year 1", eur(a.capex)],
        [f"OPEX(V) = {eur(a.opex_fixed)} + €{a.opex_per_visitor_day} × visitor-days", " / ".join(f"{YEARS[y].split()[0]} {eur(opex(Vs[y], a))}" for y in range(1, 4))],
        ["Cumulative platform cost by month 36", f"**{eur(cum36)}**, then ≈ {eur(opex(rr_V, a) / 12)}/month at the target run rate"],
        [f"Savings, from month {a.savings_start_month} (S1 vet cost −{pct(a.vet_saving[0])} → −{pct(a.vet_saving[1])} of {eur(a.vet_cost)}; S3 idle hours −{pct(a.idle_saving[0])} → −{pct(a.idle_saving[1])} of {pct(a.idle_share)} of a {eur(a.field_payroll)} field payroll)",
         f"{eur(s18)}/yr rising to {eur(s36)}/yr at month 36 — ≈ {pct(s36 / opex(rr_V, a))} of OPEX; never pays back alone"],
        [f"Contribution per visitor-day (gross − fee {eur(a.ticketing_fee)} × {a.credentials_per_visitor_day} credential − variable ops {eur(a.variable_ops)} − {pct(a.cogs_share)} cost of goods on {eur(a.on_site)} on-site)",
         f"single visit **{eur(c_single)}**, pass visit **{eur(c_pass)}**"],
        [f"Net per incremental visitor-day credited to the platform (pass contribution − €{c_single - c_pass:.0f} re-pricing of a converted single visit spread over k − 1 = {a.repeat_visits - 1} new visits, for the {pct(a.conversion_share)} of increments that come via conversion)",
         f"**{eur(net_per_incremental_vd(a))}**"],
        [f"Break-even at today's volume: annual cost OPEX({eur_m(Vs[0]).replace('€', '')}) + CAPEX ÷ {a.depreciation_years}",
         f"{eur(be['annual_cost'])} ≈ **{n(be['vd_pass'])} extra visitor-days (+{pct(be['vd_pass'] / Vs[0], 1)})** at pass contribution, "
         f"{n(be['vd_single'])} (+{pct(be['vd_single'] / Vs[0], 1)}) at single-visit contribution, "
         f"or {eur(be['on_site_sales'])} more on-site sales (+{pct(be['on_site_sales'] / be['on_site_today'])})"],
        ["Platform cost as a share of gross revenue", f"{pct(opex(Vs[0], a) / ladder(a)[0].gross, 1)} today → {pct(opex(rr_V, a) / (ladder(a)[3].gross * rr_V / Vs[3]), 1)} at the target run rate"],
    ]
    return table(["Line", "Value"], rows)


def t_sensitivity(a: Assumptions = A) -> str:
    rows_ = ladder(a)
    rr_V = a.run_rate[3] * a.open_days
    growth = rr_V - a.run_rate[2] * a.open_days
    net = net_per_incremental_vd(a)
    out = []
    for x in a.incremental_rows:
        be, c36, b36 = simulate(x, a)
        out.append([
            f"{n(x)}/yr (≈ {pct(x / rr_V)} of the year-3 run rate; {pct(x / growth)} of the Y2 → Y3 growth)",
            eur(x * net),
            f"{eur(b36)} vs. {eur(c36)}",
            f"≈ month {be} (year {math.ceil(be / 12)})" if be else f"not within {a.horizon_months // 12} years",
        ])
    be, c36, b36 = simulate(0, a)
    out.append(["Savings only", eur(savings_rate(36, a)), f"{eur(b36)} vs. {eur(c36)}", "never"])
    return table(
        [f"Incremental visitor-days credited to the platform from month {a.attribution_start_month}", "Annual attributed contribution", "Benefit vs. cost at month 36", "Cumulative break-even"],
        out,
    )


def t_okr_base(a: Assumptions = A) -> str:
    rows = ladder(a)
    return table(
        ["Key result", "Current (model)", "12-month base (Y1 run rate / year)", "36-month model (Y3)"],
        [
            ["1.1 Average visitors per day", n(rows[0].D), n(rows[1].D), n(rows[3].D)],
            ["1.2 Repeat share of households", pct(rows[0].p), pct(rows[1].p), pct(rows[3].p)],
            ["1.3 Passes' share of admissions (lower-bound assumption)", pct(rows[0].visit_share_repeat), pct(rows[1].visit_share_repeat), pct(rows[3].visit_share_repeat)],
            ["1.4 Revenue per household per year", f"€{rows[0].revenue_per_household:.0f}", f"€{rows[1].revenue_per_household:.0f} ({'+' if rows[1].revenue_per_household >= rows[0].revenue_per_household else ''}{pct(rows[1].revenue_per_household / rows[0].revenue_per_household - 1)})", f"€{rows[3].revenue_per_household:.0f} (+{pct(rows[3].revenue_per_household / rows[0].revenue_per_household - 1)})"],
            ["1.5 Weekday / weekend ratio", ratio_str(rows[0].r), ratio_str(rows[1].r), ratio_str(rows[3].r)],
            ["1.6 Season-pass renewal (model retention)", "n/a", pct(a.renewal[0]), pct(a.renewal[2])],
        ],
    )


TABLES = {
    "run-rate": t_run_rate,
    "volume": t_volume,
    "capacity": t_capacity,
    "funnel": t_funnel,
    "payback": t_payback,
    "sensitivity": t_sensitivity,
    "okr-base": t_okr_base,
}

MARK = "<!-- business-case:{name} -->"
END = "<!-- /business-case:{name} -->"


def render_all(a: Assumptions = A) -> str:
    return "\n\n".join(f"{MARK.format(name=k)}\n{f(a)}\n{END.format(name=k)}" for k, f in TABLES.items())


def replace_blocks(text: str, a: Assumptions = A) -> tuple[str, list[str]]:
    missing = []
    for name, f in TABLES.items():
        start, end = MARK.format(name=name), END.format(name=name)
        pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        if not pat.search(text):
            missing.append(name)
            continue
        text = pat.sub(lambda _m: f"{start}\n{f(a)}\n{end}", text)
    return text, missing


# --------------------------------------------------------------------------- prose tokens checked in 06 / README / 08
def expected_tokens(a: Assumptions = A) -> list[tuple[Path, str, str]]:
    """(file, row-or-section locator regex, token that must appear on that line/section)."""
    rows = ladder(a)
    win = payback_window(a)
    window = f"years {win[0]}–{win[1]}" if win else "never"
    share_today = pct(opex(yearly_volume(a)[0], a) / rows[0].gross)
    cap = capacity(a)[0]
    y3 = rows[3]
    parking_persons = a.parking_spaces * a.parking_turns * a.persons_per_car
    return [
        (DOC_06, r"^\| \*\*1\. .*1\.1 ", f"{n(rows[1].D)} / {n(8000)}"),
        (DOC_06, r"^\| \| 1\.2 ", f"{pct(rows[1].p)} / 25%"),
        (DOC_06, r"^\| \| 1\.3 ", f"{pct(rows[1].visit_share_repeat)} / 40%"),
        (DOC_06, r"^\| \| 1\.3 ", f"≈ {pct(y3.visit_share_repeat)}"),
        (DOC_06, r"^\| \| 1\.5 ", f"{ratio_str(rows[1].r)} / 0.5"),
        (README, r"^## Why this pays back", share_today),
        (README, r"^## Why this pays back", window),
        (DOC_08, r"^## 1\. ", f"×{y3.peak / cap.holds_until:.0f}"),
        (DOC_08, r"^## 1\. ", pct(parking_persons / y3.peak)),
        (DOC_08, r"^## 4\. ", window),
    ]


def check(a: Assumptions = A) -> list[str]:
    problems: list[str] = []
    if not DOC_08.exists():
        return [f"{DOC_08.relative_to(ROOT)}: missing"]
    text = DOC_08.read_text(encoding="utf-8")
    regenerated, missing = replace_blocks(text, a)
    for name in missing:
        problems.append(f"requirements/08-business-case.md: marker block '{name}' not found")
    if regenerated != text:
        problems.append("requirements/08-business-case.md: generated tables are stale — run `uv run scripts/business_case.py --write`")
    for path, locator, token in expected_tokens(a):
        if not path.exists():
            problems.append(f"{path.relative_to(ROOT)}: missing")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        loc = re.compile(locator)
        hit = [i for i, l in enumerate(lines) if loc.search(l)]
        if not hit:
            problems.append(f"{path.relative_to(ROOT)}: no line matches {locator!r} (expected '{token}')")
            continue
        # a heading locator: search until the next heading; a row locator: the row itself
        i = hit[0]
        if locator.startswith("^##"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            scope = "\n".join(lines[i:j])
        else:
            scope = lines[i]
        if token not in scope:
            problems.append(f"{path.relative_to(ROOT)}:{i + 1}: expected '{token}' from the business-case model")
    return problems


# --------------------------------------------------------------------------- self-test
def self_test(a: Assumptions = A) -> None:
    assert round(weekend_day(5_000, 0.35)) == 9_333
    assert round(weekend_day(15_000, 0.60)) == 21_000
    assert opex(1_500_000, a) == 827_500
    assert round(contribution(a)[0], 2) == 16.85 and round(contribution(a)[1], 2) == 10.85
    caps = {c.name: c.holds_until for c in capacity(a)}
    assert caps["Parking"] == 15_000
    assert round(caps["Gates"]) == 27_000
    assert round(caps["F&B seating at lunch"]) == 19_835
    ps = repeat_share(a)
    assert 0.11 < ps[1] < 0.13 and 0.39 < ps[3] < 0.42, ps
    assert [round(v) for v in yearly_volume(a)] == [1_500_000, 1_725_000, 2_400_000, 3_675_000]
    assert round(break_even_today(a)["vd_pass"]) == 81_982
    months = [simulate(x, a)[0] for x in a.incremental_rows]
    assert months == [72, 42, 37], months
    assert simulate(0, a)[0] is None
    assert payback_window(a) == (4, 6)
    text, missing = replace_blocks(render_all(a), a)
    assert not missing and text == render_all(a)
    print("self-test OK")


# --------------------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        self_test()
        return 0
    if "--check" in argv:
        problems = check()
        if problems:
            print("\n".join(problems))
            return 1
        print("business case: tables and cross-references match the model")
        return 0
    if "--write" in argv:
        text = DOC_08.read_text(encoding="utf-8")
        new, missing = replace_blocks(text)
        if missing:
            print("missing marker blocks: " + ", ".join(missing))
            return 1
        DOC_08.write_text(new, encoding="utf-8")
        print(f"wrote {len(TABLES)} tables into {DOC_08.relative_to(ROOT)}")
        return 0
    print(render_all())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
