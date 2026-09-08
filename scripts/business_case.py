"""Business-case arithmetic for requirements/08-business-case.md.

Run:  uv run scripts/business_case.py            print the generated tables
      uv run scripts/business_case.py --write    insert them between the markers in requirements/08
      uv run scripts/business_case.py --check    verify 08, 06, README and the other documents that quote
                                                 a derived number against the model (called by lint_docs.py)
      uv run scripts/business_case.py --self-test

Every derived number in requirements/08 comes from the ASSUMPTIONS block below.
Season 1 replaces the assumptions with measured values (requirements/08 §0);
edit the block, run --write, and the tables in 08 follow. Stdlib only.

Model in one paragraph. Ladder values are end-of-year run rates (visitor-days per
day); yearly volume is the mean of adjacent run rates × open days. The weekday /
weekend ratio r gives the weekend-day average W = 7D / (5r + 2) and the peak day
W × s. Households are counted, not shared: each year the repeaters R are last
year's repeaters retained (pass holders by pass renewal, the rest by account
retention) plus last year's single-visit households converted (organic + flywheel,
flywheel = adoption × opt-in × nudge reach × return); the year's household visits
HV = V ÷ party size then give H = HV − R(k − 1) unique households, S = H − R
singles, p = R ÷ H, and the singles not retained from last year are the new
households marketing must acquire. Pass holders are R × pass conversion; their
visits are priced as pass visits, every other visit as a single visit. Payback is
platform payback only, undiscounted: cost = CAPEX + OPEX(V); benefit = savings
from Phase 2 plus incremental visitor-days credited to the platform, ramping with
the roadmap (S4 from month 30, S5 at experiment depth until its month-42 readout),
at contribution before the ticketing fee (the fee already sits in OPEX), minus the
re-pricing of the single visit a converted household used to make.

  cohort, per year y                                  R_{y-1}: pass × renewal + no-pass × account retention
  ┌──────────────┐  retained ──────────────────────▶  ┌────────────┐
  │ R_{y-1}, S_{y-1} │                                 │ R_y        │──▶ pass_y = R_y × pass_conversion
  └──────────────┘  converted = S_{y-1}(organic+flywheel)└────────────┘
  HV_y = V_y ÷ party        H_y = HV_y − R_y(k−1)      S_y = H_y − R_y      A_y = S_y − S_{y-1}(1−conv)×single_return
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC_08 = ROOT / "requirements/08-business-case.md"
DOC_04 = ROOT / "requirements/04-non-functional-requirements.md"
DOC_05 = ROOT / "requirements/05-assumptions-and-constraints.md"
DOC_06 = ROOT / "requirements/06-suggested-okrs.md"
DOC_07 = ROOT / "requirements/07-risks-and-mitigations.md"
README = ROOT / "README.md"
EDGE = ROOT / "hld/core/edge-and-connectivity.md"
AIP = ROOT / "hld/ai-platform/README.md"
S4 = ROOT / "hld/scenarios/guest-companion/README.md"
S5 = ROOT / "hld/scenarios/dynamic-family-passes/README.md"

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

    # Cohort funnel (requirements/08 §3). Y1..Y3 unless stated; Y0 = today.
    organic_repeat: float = 0.10       # p today (OKR 1.2 current estimate)
    habit_retention_today: float = 0.50  # share of today's repeaters who repeat again next year
    adoption: tuple = (0.25, 0.45, 0.60)      # households creating an itinerary
    opt_in: tuple = (0.40, 0.55, 0.75)        # of those, opening an account
    nudge_reach: tuple = (0.30, 0.50, 0.90)   # of those, reached by a nudge they act on (plain offer mail before Phase 3)
    return_rate: tuple = (0.40, 0.50, 0.70)   # of those, back within 12 months
    pass_conversion: tuple = (0.80, 0.75, 0.70, 0.70)  # Y0..Y3: share of repeaters holding a season pass
    pass_renewal: tuple = (0.60, 0.65, 0.70)  # pass-holding repeaters renewing (PassRenewed, OKR 1.6)
    account_retention: tuple = (0.40, 0.45, 0.50)  # repeaters without a pass repeating again (accounts)
    single_return: float = 0.15        # single-visit households coming back once next year (once-a-year habit)

    # Revenue per visitor-day, gross (requirements/08 §0)
    admission_single: float = 15.0
    admission_pass: float = 9.0        # season pass at 1.8 single admissions per person, used k = 3 times
    on_site: float = 6.0
    cogs_share: float = 0.50           # A15 — cost of goods on on-site sales
    variable_ops: float = 1.0          # A15 — per visitor-day
    ticketing_fee: float = 0.15        # A15 — per credential; already inside OPEX(V)
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
    attribution_start_month: int = 30  # Phase 3 levers live (S4 nudges, S5 experiment blocks)
    attribution_full_month: int = 42   # S5 readout; full rate only after a Go
    attribution_plateau: float = 0.5   # share of the incremental rate reached at the readout
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
    lunch_window_share: float = 0.80   # share of the day's visitor-days on site at some point during the lunch window
    seated_lunch_uptake: float = 0.55  # of those, taking a seated lunch
    gate_lanes: int = 6
    scans_per_lane_hour: int = 900
    persons_per_scan: float = 2.0      # blended: single tickets 1, family passes up to 3.5 per scan
    rides: int = 40
    riders_per_hour: tuple = (150, 300)
    ride_hours: int = 8
    m2_per_person: float = 3.3         # Fruin LOS C

    # Market (requirements/08 §5 sanity check)
    catchment_penetration: float = 0.20  # share of households with children in the 2-hour catchment visiting in a year


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


def m(x: float) -> str:
    """Millions without a currency sign: 1.7M."""
    return f"{x / 1_000_000:.1f}M"


def k(x: float) -> str:
    return f"{x / 1_000:.0f}k"


def ratio_str(x: float) -> str:
    return f"{x:.2f}"


def delta_pct(cur: float, base: float) -> str:
    d = cur / base - 1
    return f"{'+' if d >= 0 else ''}{pct(d)}"


# --------------------------------------------------------------------------- model
def weekend_day(D: float, r: float, a: Assumptions = A) -> float:
    """Weekend-day average W from the daily average D: weekly = W(5r + 2) = 7D."""
    return 7 * D / (5 * r + 2)


def opex(V: float, a: Assumptions = A) -> float:
    return a.opex_fixed + a.opex_per_visitor_day * V


def contribution(a: Assumptions = A, include_fee: bool = True) -> tuple[float, float]:
    """Contribution per visitor-day: (single visit, pass visit).

    include_fee=False is the attribution view: the ticketing fee already sits in OPEX(V),
    so charging it again against incremental visits would count it twice.
    """
    fee = a.ticketing_fee * a.credentials_per_visitor_day if include_fee else 0.0
    variable = fee + a.variable_ops + a.cogs_share * a.on_site
    return a.admission_single + a.on_site - variable, a.admission_pass + a.on_site - variable


def organic_conversion(a: Assumptions = A) -> float:
    """Steady state today: R0 = R0 × retention + S0 × g  →  g = R0(1 − retention) ÷ S0."""
    p0 = a.organic_repeat
    return p0 * (1 - a.habit_retention_today) / (1 - p0)


def yearly_volume(a: Assumptions = A) -> list[float]:
    """Visitor-days per year: Y0 at today's run rate; Y1..Y3 = mean of adjacent run rates × open days."""
    rr = a.run_rate
    return [rr[0] * a.open_days] + [(rr[y - 1] + rr[y]) / 2 * a.open_days for y in range(1, 4)]


@dataclass
class Cohort:
    label: str
    V: float
    HV: float          # household visits
    H: float           # unique households
    R: float           # repeating households (≥ 2 visits)
    S: float           # single-visit households
    R_pass: float      # repeaters holding a season pass
    retained: float
    converted: float
    new: float         # households marketing must bring (not visiting last year)
    flywheel: float    # flywheel conversion rate this year

    @property
    def p(self) -> float:
        return self.R / self.H

    @property
    def pass_vd(self) -> float:
        return self.R_pass * A_K[0] * A_K[1]

    @property
    def repeat_nopass_vd(self) -> float:
        return (self.R - self.R_pass) * A_K[0] * A_K[1]

    @property
    def single_vd(self) -> float:
        return self.S * A_K[1]


A_K: tuple = (A.repeat_visits, A.party_size)  # set per call in cohorts(); module default for property access


def cohorts(a: Assumptions = A) -> list[Cohort]:
    """Count-based household cohorts, Y0..Y3."""
    global A_K
    A_K = (a.repeat_visits, a.party_size)
    kk = a.repeat_visits
    Vs = yearly_volume(a)
    g = organic_conversion(a)
    HV0 = Vs[0] / a.party_size
    p0 = a.organic_repeat
    H0 = HV0 / (p0 * kk + 1 - p0)
    R0 = p0 * H0
    out = [Cohort(YEARS[0], Vs[0], HV0, H0, R0, H0 - R0, R0 * a.pass_conversion[0], R0, 0.0, 0.0, 0.0)]
    for y in range(1, 4):
        prev = out[-1]
        fly = a.adoption[y - 1] * a.opt_in[y - 1] * a.nudge_reach[y - 1] * a.return_rate[y - 1]
        conv_rate = min(1.0, g + fly)
        retained = prev.R_pass * a.pass_renewal[y - 1] + (prev.R - prev.R_pass) * a.account_retention[y - 1]
        converted = prev.S * conv_rate
        R = retained + converted
        HV = Vs[y] / a.party_size
        H = HV - R * (kk - 1)
        S = H - R
        singles_back = prev.S * (1 - conv_rate) * a.single_return
        new = S - singles_back
        out.append(Cohort(YEARS[y], Vs[y], HV, H, R, S, R * a.pass_conversion[y], retained, converted, new, fly))
    return out


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
    c: Cohort
    gross: float
    contribution: float

    @property
    def V(self) -> float:
        return self.c.V

    @property
    def pass_share(self) -> float:
        return self.c.pass_vd / self.c.V

    @property
    def revenue_per_vd(self) -> float:
        return self.gross / self.c.V

    @property
    def revenue_per_household(self) -> float:
        return self.gross / self.c.H


def ladder(a: Assumptions = A) -> list[YearRow]:
    rows = []
    c_single, c_pass = contribution(a)
    single_gross, pass_gross = a.admission_single + a.on_site, a.admission_pass + a.on_site
    for y, c in enumerate(cohorts(a)):
        D, r = a.run_rate[y], a.ratio[y]
        W = weekend_day(D, r, a)
        peak = W * a.peak_factor
        gross = (c.single_vd + c.repeat_nopass_vd) * single_gross + c.pass_vd * pass_gross
        contrib = (c.single_vd + c.repeat_nopass_vd) * c_single + c.pass_vd * c_pass
        rows.append(YearRow(YEARS[y], D, r, W, W * r, peak, peak * a.peak_hour_share, peak * a.on_site_share, c, gross, contrib))
    return rows


# --------------------------------------------------------------------------- capacity
@dataclass
class Constraint:
    name: str
    assumption: str
    arithmetic: str
    holds_until: float | None      # peak-day visitor-days; None = not a hard limit / not assessed
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
    fnb = meals / (a.lunch_window_share * a.seated_lunch_uptake)
    gates_scans = a.gate_lanes * a.scans_per_lane_hour
    gates = gates_scans * a.persons_per_scan / a.peak_hour_share
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
            f"Binds. Target peak ≈ {n(y3.peak)} needs ≈ ×{y3.peak / parking:.0f} spaces or a car share "
            f"≤ {pct(parking_persons / y3.peak)}: park-and-ride / coach share, plus pass-holder reservations and "
            f"timed entry on capacity-managed days (FR-1.7) and quiet-day shaping (S5). A cap redistributes arrivals; "
            f"it adds no space",
        ),
        Constraint(
            "F&B seating at lunch",
            f"{n(a.fnb_seats)} seats × {a.fnb_turns} turns 11:30–14:30 = {n(meals)} meals; "
            f"{pct(a.lunch_window_share)} of the day's visitor-days are on site at some point in that window × "
            f"{pct(a.seated_lunch_uptake)} of those take a seated lunch (→ `PurchaseRecorded`, queue counters)",
            f"{n(meals)} ÷ ({a.lunch_window_share} × {a.seated_lunch_uptake}) = **{n(fnb)}**",
            fnb,
            "Binds. Companion steers lunch times and under-used outlets (S4); spend per zone shows where; "
            "seats or a longer window are the estate's (§5)",
        ),
        Constraint(
            "Gates",
            f"{a.gate_lanes} lanes × {n(a.scans_per_lane_hour)} scans/h × {a.persons_per_scan} persons per scan "
            f"(blended: single tickets 1, family passes up to {a.party_size}); {pct(a.peak_hour_share)} of arrivals "
            f"in the peak hour (→ `GateEntered.persons_admitted`)",
            f"{n(gates_scans)}/h × {a.persons_per_scan} ÷ {a.peak_hour_share} = **{n(gates)}**",
            gates,
            f"Holds: peak hour ≈ {n(y3.peak_hour)} persons/h against ≈ {n(gates_scans * a.persons_per_scan)}; "
            f"timed-entry slots (FR-1.7) keep the margin if persons per scan turns out lower",
        ),
        Constraint(
            "Rides",
            f"{a.rides} historic rides × {a.riders_per_hour[0]}–{a.riders_per_hour[1]} riders/h × {a.ride_hours} h "
            f"= {n(rides_lo / 1000)}k–{n(rides_hi / 1000)}k rides/day (→ ride cycle counters)",
            f"{rides_lo / y3.peak:.1f}–{rides_hi / y3.peak:.1f} rides per visitor on the target peak day",
            None,
            "Not a hard limit but the experience constraint: OKR 2.2 (p90 queue ≤ 20 min) breaks first, and on the "
            "popular rides long before the average says so; S3/S4 load spreading is the lever",
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
            f"peak-hour gate rate ≈ {y3.peak_hour / a.persons_per_scan / 3600:.1f} scans/s",
            None,
            "Hold ([capacity table](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class))",
        ),
        Constraint(
            "Not assessed",
            "egress and emergency evacuation capacity, toilets, kitchen throughput, access roads and local choke points",
            "no figures in this document",
            None,
            "Open until the Phase 0 site survey (A14); any of them can bind before the rows above",
        ),
    ]


def parking_verdict(a: Assumptions = A) -> tuple[float, float]:
    """(× spaces needed, max car share) for the target peak on current parking."""
    cap = capacity(a)[0]
    y3 = ladder(a)[3]
    parking_persons = a.parking_spaces * a.parking_turns * a.persons_per_car
    return y3.peak / cap.holds_until, parking_persons / y3.peak


# --------------------------------------------------------------------------- payback
def savings_rate(month: int, a: Assumptions = A) -> float:
    """Annual savings rate at a given month: ramps from the 12-month to the 36-month OKR targets."""
    if month < a.savings_start_month:
        return 0.0
    s12 = a.vet_cost * a.vet_saving[0] + a.field_payroll * a.idle_share * a.idle_saving[0]
    s36 = a.vet_cost * a.vet_saving[1] + a.field_payroll * a.idle_share * a.idle_saving[1]
    t = min(1.0, (month - a.savings_start_month) / (36 - a.savings_start_month))
    return s12 + (s36 - s12) * t


def attribution_ramp(month: int, a: Assumptions = A) -> float:
    """Share of the incremental rate credited in a month: 0 before Phase 3, linear to the plateau at the
    S5 readout (S4 nudges + experiment blocks only), full rate after a Go."""
    if month <= a.attribution_start_month:
        return 0.0
    if month <= a.attribution_full_month:
        return a.attribution_plateau * (month - a.attribution_start_month) / (a.attribution_full_month - a.attribution_start_month)
    return 1.0


def net_per_incremental_vd(a: Assumptions = A) -> float:
    """Contribution before the fee per incremental visitor-day: pass-holding converts pay the pass
    contribution minus the re-pricing of their former single visit spread over k − 1 new visits;
    the other incremental visits pay the single-visit contribution."""
    c_single, c_pass = contribution(a, include_fee=False)
    debit = (c_single - c_pass) / (a.repeat_visits - 1)
    pc = a.pass_conversion[3]
    return pc * (c_pass - a.conversion_share * debit) + (1 - pc) * c_single


def simulate(incremental_vd: float, a: Assumptions = A) -> tuple[int | None, float, float]:
    """Return (break-even month or None, cumulative cost at 36, cumulative benefit at 36)."""
    Vs = yearly_volume(a)
    run_rate_V = a.run_rate[3] * a.open_days
    cost = a.capex
    benefit = 0.0
    be = None
    cost36 = benefit36 = 0.0
    net = net_per_incremental_vd(a)
    for mo in range(1, a.horizon_months + 1):
        V = Vs[min(3, (mo - 1) // 12 + 1)] if mo <= 36 else run_rate_V
        cost += opex(V, a) / 12
        benefit += savings_rate(mo, a) / 12
        benefit += incremental_vd * net * attribution_ramp(mo, a) / 12
        if be is None and benefit >= cost:
            be = mo
        if mo == 36:
            cost36, benefit36 = cost, benefit
    return be, cost36, benefit36


def payback_window(a: Assumptions = A) -> tuple[int, int] | None:
    """(earliest, latest) break-even year over the sensitivity rows that do break even."""
    months = [simulate(x, a)[0] for x in a.incremental_rows]
    months = [mo for mo in months if mo is not None]
    if not months:
        return None
    return math.ceil(min(months) / 12), math.ceil(max(months) / 12)


def break_even_today(a: Assumptions = A) -> dict[str, float]:
    V0 = yearly_volume(a)[0]
    annual_cost = opex(V0, a) + a.capex / a.depreciation_years
    c_single, c_pass = contribution(a, include_fee=False)
    return {
        "annual_cost": annual_cost,
        "vd_pass": annual_cost / c_pass,
        "vd_single": annual_cost / c_single,
        "on_site_sales": annual_cost / (1 - a.cogs_share),
        "on_site_today": V0 * a.on_site,
    }


def required_catchment(a: Assumptions = A) -> float:
    return cohorts(a)[3].H / a.catchment_penetration


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
            [f"Visitor-days (mean of adjacent run rates × {a.open_days} open days)", *[m(r.V) for r in rows]],
            ["Repeat share of households p (OKR 1.2) — from the cohort model in §3", *[pct(r.c.p) for r in rows]],
            [f"Unique households H (household visits ÷ {a.party_size} people, k = {a.repeat_visits} visits per repeater)", *[k(r.c.H) for r in rows]],
            ["Repeat households R", *[k(r.c.R) for r in rows]],
            ["— of which pass holders (R × pass conversion)", *[k(r.c.R_pass) for r in rows]],
            ["Single-visit households S", *[k(r.c.S) for r in rows]],
            ["**New households marketing must bring** (not visiting last year)", "—", *[f"**{k(r.c.new)}**" for r in rows[1:]]],
            ["Pass visitor-days — share of all visits (OKR 1.3 model)", *[f"{m(r.c.pass_vd)} — **{pct(r.pass_share)}**" for r in rows]],
            ["Repeat visitor-days without a pass (priced as single visits)", *[m(r.c.repeat_nopass_vd) for r in rows]],
            ["Single visitor-days", *[m(r.c.single_vd) for r in rows]],
            [f"Gross revenue (single or no-pass visit {eur(a.admission_single + a.on_site)}, pass visit {eur(a.admission_pass + a.on_site)})",
             *[eur_m(r.gross) for r in rows]],
            ["Revenue per visitor-day (OKR 1.4 primary line)", *[f"€{r.revenue_per_vd:.1f}" for r in rows]],
            ["Revenue per unique household per year (OKR 1.4 second line — an estimate, H is modelled)",
             *[f"€{r.revenue_per_household:.0f}" + ("" if r is base else f" ({delta_pct(r.revenue_per_household, base.revenue_per_household)})") for r in rows]],
            [f"Contribution (single {eur(contribution(a)[0])}, pass {eur(contribution(a)[1])} per visitor-day, fee included)",
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
    cs = cohorts(a)
    g = organic_conversion(a)
    stages = [
        ("Companion adoption", "households that create an itinerary", a.adoption, "`ItineraryCreated` ÷ households admitted", "S4 FAQ (Phase 1) → day planning (Phase 2)"),
        ("Opt-in", "of those, households opening an account", a.opt_in, "account opt-in (FR-1.6) ÷ companion households", "the companion gives a reason to keep an account"),
        ("Nudge reach", "of those, reached by a nudge they act on (click or visit, not e-mail opens — privacy proxies inflate opens)", a.nudge_reach, "`NudgeSent` with a click ÷ accounts", "plain offer mail from the ticketing platform before Phase 3; S4 personalised nudges from month 30"),
        ("Return", "of those, back within 12 months", a.return_rate, "`GateEntered` of the household after a nudge", "quiet-day offer and season-pass offer in the nudge"),
        ("Pass conversion", f"of repeaters, holding a season pass (today {pct(a.pass_conversion[0])})", a.pass_conversion[1:], "pass `TicketPurchased` or redeemed upgrade credit ÷ repeating households", "drives OKR 1.3 and the revenue mix; falls at first because nudge-won repeaters start without a pass"),
        ("Pass renewal", "of pass-holding repeaters, renewing (OKR 1.6)", a.pass_renewal, "`PassRenewed` ÷ passes expiring", "executed by the ticketing platform; the upgrade credit and the nudges feed it"),
        ("Account retention", "of repeaters without a pass, repeating again", a.account_retention, "repeat `GateEntered` across years for accounts; anonymous repeaters by survey (A14)", "S4 nudges; an assumption for the anonymous share"),
        ("Single return", "of single-visit households not converted, back once next year", (a.single_return,) * 3, "accounts across years; exit survey", "the once-a-year habit; constant"),
    ]
    rows = [[name, what, *[pct(v[y]) for y in range(3)], event, ramp] for name, what, v, event, ramp in stages]
    rows.append(["**Flywheel conversion** (adoption × opt-in × reach × return)", "share of last year's single-visit households converted this year", *[pct(c.flywheel, 1) for c in cs[1:]], "derived", ""])
    rows.append(["**Organic conversion**", f"today's steady state: p = {pct(a.organic_repeat)} with retention {pct(a.habit_retention_today)}", *[pct(g, 1)] * 3, "exit survey (A14)", "constant"])
    rows.append(["**Repeaters R** = retained + converted (households)", f"Y0 = {k(cs[0].R)}", *[f"**{k(c.R)}** ({k(c.retained)} + {k(c.converted)})" for c in cs[1:]], "identified households with ≥ 2 visits", ""])
    rows.append(["**Repeat share p** = R ÷ H", f"Y0 = {pct(cs[0].p)}", *[f"**{pct(c.p)}**" for c in cs[1:]], "OKR 1.2", "growth dilutes p: new households arrive faster than the flywheel converts them"])
    return table(["Rate", "Meaning", "Y1", "Y2", "Y3", "Measured by", "Why it moves"], rows)


def t_payback(a: Assumptions = A) -> str:
    Vs = yearly_volume(a)
    rr_V = a.run_rate[3] * a.open_days
    c_single, c_pass = contribution(a)
    nf_single, nf_pass = contribution(a, include_fee=False)
    s18 = savings_rate(a.savings_start_month, a)
    s36 = savings_rate(36, a)
    be = break_even_today(a)
    cum36 = a.capex + sum(opex(Vs[y], a) for y in range(1, 4))
    rows_ = ladder(a)
    rows = [
        ["CAPEX (requirements/04), all in year 1", eur(a.capex)],
        [f"OPEX(V) = {eur(a.opex_fixed)} + €{a.opex_per_visitor_day} × visitor-days (the €{a.ticketing_fee} ticketing fee per visitor-day is inside)", " / ".join(f"{YEARS[y].split()[0]} {eur(opex(Vs[y], a))}" for y in range(1, 4))],
        ["Cumulative platform cost by month 36", f"**{eur(cum36)}**, then ≈ {eur(opex(rr_V, a) / 12)}/month at the target run rate"],
        ["**Do nothing** (baseline the benefit is measured against)", "no CAPEX, no OPEX, no savings; attendance moves only with the base price, marketing and the season — the platform's benefit below is the difference to this line"],
        [f"Savings, from month {a.savings_start_month} (S1 vet cost −{pct(a.vet_saving[0])} → −{pct(a.vet_saving[1])} of {eur(a.vet_cost)}; S3 idle hours −{pct(a.idle_saving[0])} → −{pct(a.idle_saving[1])} of {pct(a.idle_share)} of a {eur(a.field_payroll)} field payroll)",
         f"{eur(s18)}/yr rising to {eur(s36)}/yr at month 36 — ≈ {pct(s36 / opex(rr_V, a))} of OPEX; never pays back alone"],
        [f"Contribution per visitor-day, fee included (gross − fee {eur(a.ticketing_fee)} × {a.credentials_per_visitor_day} credential − variable ops {eur(a.variable_ops)} − {pct(a.cogs_share)} cost of goods on {eur(a.on_site)} on-site)",
         f"single visit **{eur(c_single)}**, pass visit **{eur(c_pass)}** — the figures the OKRs and the S5 guardrail use"],
        ["Contribution per visitor-day **before the fee** (the fee is already in OPEX(V) — counting it here too would charge it twice)",
         f"single visit {eur(nf_single)}, pass visit {eur(nf_pass)} — used for attribution and break-even only"],
        [f"Net per incremental visitor-day credited to the platform ({pct(a.pass_conversion[3])} of incremental visits by pass holders at pass contribution minus €{nf_single - nf_pass:.0f} re-pricing of a converted single visit spread over k − 1 = {a.repeat_visits - 1} new visits for the {pct(a.conversion_share)} that come via conversion; the rest at single-visit contribution)",
         f"**{eur(net_per_incremental_vd(a))}**"],
        [f"Attribution ramp (roadmap gates): 0 until month {a.attribution_start_month}; linear to {pct(a.attribution_plateau)} of the rate at month {a.attribution_full_month} (S4 nudges live, S5 only on experiment blocks); {pct(1.0)} after the S5 Go",
         f"the sensitivity below applies it month by month"],
        [f"Break-even at today's volume: annual cost OPEX({m(Vs[0])}) + CAPEX ÷ {a.depreciation_years}",
         f"{eur(be['annual_cost'])} ≈ **{n(be['vd_pass'])} extra visitor-days (+{pct(be['vd_pass'] / Vs[0], 1)})** at pass contribution before the fee, "
         f"{n(be['vd_single'])} (+{pct(be['vd_single'] / Vs[0], 1)}) at single-visit contribution, "
         f"or {eur(be['on_site_sales'])} more on-site sales (+{pct(be['on_site_sales'] / be['on_site_today'])})"],
        ["Platform cost as a share of gross revenue", f"{pct(opex(Vs[0], a) / rows_[0].gross, 1)} today → {pct(opex(rr_V, a) / (rows_[3].gross * rr_V / Vs[3]), 1)} at the target run rate"],
    ]
    return table(["Line", "Value"], rows)


def t_sensitivity(a: Assumptions = A) -> str:
    rr_V = a.run_rate[3] * a.open_days
    growth = rr_V - a.run_rate[2] * a.open_days
    net = net_per_incremental_vd(a)
    out = []
    for x in a.incremental_rows:
        be, c36, b36 = simulate(x, a)
        out.append([
            f"{n(x)}/yr at full rate (≈ {pct(x / rr_V)} of the year-3 run rate; {pct(x / growth)} of the Y2 → Y3 growth)",
            eur(x * net),
            f"{eur(b36)} vs. {eur(c36)}",
            f"≈ month {be} (year {math.ceil(be / 12)})" if be else f"not within {a.horizon_months // 12} years",
        ])
    be, c36, b36 = simulate(0, a)
    out.append(["Savings only", eur(savings_rate(36, a)), f"{eur(b36)} vs. {eur(c36)}", "never"])
    return table(
        [f"Incremental visitor-days credited to the platform (ramped from month {a.attribution_start_month}, full after month {a.attribution_full_month})", "Annual attributed contribution at full rate", "Benefit vs. cost at month 36", "Cumulative break-even"],
        out,
    )


def t_okr_base(a: Assumptions = A) -> str:
    rows = ladder(a)
    return table(
        ["Key result", "Current (model)", "12-month base (Y1 run rate / year)", "36-month model (Y3)"],
        [
            ["1.1 Average visitors per day", n(rows[0].D), n(rows[1].D), n(rows[3].D)],
            ["1.2 Repeat share of households", pct(rows[0].c.p), pct(rows[1].c.p), pct(rows[3].c.p)],
            ["1.3 Passes' share of admissions (visitor-days)", pct(rows[0].pass_share), pct(rows[1].pass_share), pct(rows[3].pass_share)],
            ["1.4 Revenue per visitor-day (primary)", f"€{rows[0].revenue_per_vd:.1f}", f"€{rows[1].revenue_per_vd:.1f} ({delta_pct(rows[1].revenue_per_vd, rows[0].revenue_per_vd)})", f"€{rows[3].revenue_per_vd:.1f} ({delta_pct(rows[3].revenue_per_vd, rows[0].revenue_per_vd)})"],
            ["1.4 Revenue per unique household per year (estimate)", f"€{rows[0].revenue_per_household:.0f}", f"€{rows[1].revenue_per_household:.0f} ({delta_pct(rows[1].revenue_per_household, rows[0].revenue_per_household)})", f"€{rows[3].revenue_per_household:.0f} ({delta_pct(rows[3].revenue_per_household, rows[0].revenue_per_household)})"],
            ["1.5 Weekday / weekend ratio", ratio_str(rows[0].r), ratio_str(rows[1].r), ratio_str(rows[3].r)],
            ["1.6 Season-pass renewal (model)", "n/a", pct(a.pass_renewal[0]), pct(a.pass_renewal[2])],
        ],
    )


def t_catchment(a: Assumptions = A) -> str:
    cs = cohorts(a)
    return table(
        ["Market sanity check (assumption → measured by)", "Value"],
        [
            ["Unique households in year 3", f"{k(cs[3].H)} (×{cs[3].H / cs[0].H:.1f} vs. today) ≈ {m(cs[3].H * a.party_size)} people"],
            ["New households marketing must bring in year 3 (not visiting the year before)", f"{k(cs[3].new)}"],
            [f"Required catchment at {pct(a.catchment_penetration)} yearly penetration of households with children within ≈ 2 h (→ postcode survey at the gate, ticketing addresses)",
             f"≈ **{m(required_catchment(a))} households** — the scale of a large metropolitan area or a tourist region, a site fact the estate must confirm (R18)"],
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
    "catchment": t_catchment,
}

MARK = "<!-- business-case:{name} -->"
END = "<!-- /business-case:{name} -->"


def render_all(a: Assumptions = A) -> str:
    return "\n\n".join(f"{MARK.format(name=key)}\n{f(a)}\n{END.format(name=key)}" for key, f in TABLES.items())


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


# --------------------------------------------------------------------------- prose tokens checked across the documents
def expected_tokens(a: Assumptions = A) -> list[tuple[Path, str, str]]:
    """(file, locator regex, token). A locator starting with '^##' scopes to that section; otherwise to the line."""
    rows = ladder(a)
    cs = cohorts(a)
    win = payback_window(a)
    window = f"years {win[0]}–{win[1]}" if win else "never"
    share_today = pct(opex(yearly_volume(a)[0], a) / rows[0].gross)
    y3, y1, y0 = rows[3], rows[1], rows[0]
    x_spaces, car_share = parking_verdict(a)
    rr_V = a.run_rate[3] * a.open_days
    growth = rr_V - a.run_rate[2] * a.open_days
    fnb = capacity(a)[1].holds_until
    peak_hour_scans = y3.peak_hour / a.persons_per_scan
    return [
        # requirements/06 — OKR base cells and model notes
        (DOC_06, r"^\| \*\*1\. .*1\.1 ", f"{n(y1.D)} / {n(8000)}"),
        (DOC_06, r"^\| \| 1\.2 ", f"{pct(y1.c.p)} / 25%"),
        (DOC_06, r"^\| \| 1\.2 ", f"model: ≈ {pct(y3.c.p)}"),
        (DOC_06, r"^\| \| 1\.3 ", f"{pct(y1.pass_share)} / 40%"),
        (DOC_06, r"^\| \| 1\.3 ", f"model: ≈ {pct(y3.pass_share)}"),
        (DOC_06, r"^\| \| 1\.5 ", f"{ratio_str(y1.r)} / 0.5"),
        (DOC_06, r"^¹ ", f"party size of {a.party_size}"),
        # README — Why this pays back
        (README, r"^## Why this pays back", share_today),
        (README, r"^## Why this pays back", window),
        (README, r"^## Why this pays back", f"{pct(a.incremental_rows[2] / growth)} of the growth between year 2 and year 3"),
        # requirements/08 prose
        (DOC_08, r"^# 08 ", window),
        (DOC_08, r"^## 0\. ", f"party size of {a.party_size}"),
        (DOC_08, r"^## 0\. ", f"≈ {m(cs[3].V)}"),
        (DOC_08, r"^## 1\. ", f"×{x_spaces:.0f}"),
        (DOC_08, r"^## 1\. ", pct(car_share)),
        (DOC_08, r"^## 1\. ", f"near {n(y3.peak)}"),
        (DOC_08, r"^## 1\. ", f"holds {n(fnb)}"),
        (DOC_08, r"^## 2\. ", f"×{y3.W / y0.W:.2f}"),
        (DOC_08, r"^## 2\. ", f"×{(5 * y3.r + 2) / (5 * y0.r + 2):.2f}"),
        (DOC_08, r"^## 2\. ", f"×{cs[3].H / cs[0].H:.1f}"),
        (DOC_08, r"^## 2\. ", f"×{(cs[3].HV / cs[3].H) / (cs[0].HV / cs[0].H):.1f}"),
        (DOC_08, r"^## 2\. ", f"{pct(y3.pass_share)} of visits"),
        (DOC_08, r"^## 2\. ", delta_pct(y3.revenue_per_household, y0.revenue_per_household)),
        (DOC_08, r"^## 2\. ", f"×{y3.contribution / y0.contribution:.1f}"),
        (DOC_08, r"^## 3\. ", f"{pct(y3.c.p)} in year 3"),
        (DOC_08, r"^## 4\. ", window),
        (DOC_08, r"^## 4\. ", f"{n(a.incremental_rows[2])} incremental visitor-days"),
        (DOC_08, r"^## 4\. ", f"{pct(a.incremental_rows[2] / growth)} of the year-2-to-year-3 growth"),
        (DOC_08, r"^## 4\. ", f"{pct(savings_rate(36, a) / opex(rr_V, a))} of running cost"),
        (DOC_08, r"^## 4\. ", f"{pct(a.opex_fixed * 500 / 580 / opex(rr_V, a))} of OPEX"),
        (DOC_08, r"^## 5\. ", f"≈ {share_today} of revenue today"),
        (DOC_08, r"^## 5\. ", f"{pct(opex(rr_V, a) / (y3.gross * rr_V / y3.V), 1)} at target"),
        (DOC_08, r"^## 5\. ", f"×{cs[3].H / cs[0].H:.1f} unique households"),
        (DOC_08, r"^## 5\. ", f"≤ {pct(car_share)}"),
        # other documents quoting derived numbers
        (DOC_04, r"^\| NFR-SCL-1 ", f"≈ {n(y3.peak)}"),
        (DOC_04, r"^\| NFR-SCL-1 ", f"≈ {n(peak_hour_scans)} gate scans"),
        (DOC_05, r"^\| A9 ", f"{a.party_size} persons"),
        (DOC_07, r"^\| R17 ", "parking and lunch seating"),
        (DOC_07, r"^\| R18 ", f"×{cs[3].H / cs[0].H:.1f} unique households"),
        (DOC_07, r"^\| R18 ", f"≈ {m(required_catchment(a))} households"),
        (EDGE, r"^\| \*\*Gate readers\*\* ", f"≈ {n(peak_hour_scans)} scans in the peak hour"),
        (EDGE, r"^\| \*\*Gate readers\*\* ", f"≈ {n(y3.peak)} visitor-days"),
        (EDGE, r"^\| Critical ", f"up to {n(y3.peak * 2 / a.persons_per_scan)} scans, {peak_hour_scans / 3600:.1f}/s"),
        (EDGE, r"^- Gate scans: ", f"≈ {n(y3.peak)} in + out"),
        (EDGE, r"^- Gate scans: ", f"≈ {n(peak_hour_scans)} scans in the peak hour → {peak_hour_scans / 3600:.1f}/s"),
        (AIP, r"^\| \*\*Business guardrails\*\* ", f"{eur(a.on_site)} on-site spend per visitor-day"),
        (S4, r"^\*\*Moves:\*\* ", f"{pct(y0.c.p)} → {pct(y1.c.p)} base / 25% stretch → 40% target, model ≈ {pct(y3.c.p)}"),
        (S4, r"^\*\*Moves:\*\* ", f"{pct(y0.pass_share)} → {pct(y1.pass_share)} / 40% → ≥ 50% target, model ≈ {pct(y3.pass_share)}"),
        (S5, r"^\*\*Moves:\*\* ", f"{ratio_str(y0.r)} → {ratio_str(y1.r)} base / 0.5 stretch → {ratio_str(y3.r)}"),
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
        i = hit[0]
        if locator.startswith("^#"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            scope = "\n".join(lines[i:j])
        else:
            scope = lines[i]
        if token not in scope:
            problems.append(f"{path.relative_to(ROOT)}:{i + 1}: expected '{token}' from the business-case model")
    return problems


# --------------------------------------------------------------------------- self-test: invariants, not today's outputs
PESSIMISTIC = replace(A, adoption=(0.15, 0.30, 0.45), return_rate=(0.30, 0.40, 0.50), pass_renewal=(0.50, 0.55, 0.60), on_site=4.0)
OPTIMISTIC = replace(A, adoption=(0.35, 0.55, 0.70), return_rate=(0.50, 0.60, 0.80), pass_conversion=(0.80, 0.80, 0.80, 0.85), run_rate=(5_000, 7_000, 10_000, 15_000))


def invariants(a: Assumptions) -> None:
    cs, rows = cohorts(a), ladder(a)
    Vs = yearly_volume(a)
    for c, row, V in zip(cs, rows, Vs):
        assert abs(c.V - V) < 1e-6
        assert abs(c.pass_vd + c.repeat_nopass_vd + c.single_vd - V) < 1e-3 * V, "visitor-days split must add up"
        assert abs(c.R + c.S - c.H) < 1e-6 and abs(c.R * a.repeat_visits + c.S - c.HV) < 1e-6
        assert 0 <= c.p <= 1 and 0 <= c.R_pass <= c.R and c.new >= 0 and c.S >= 0, c
        assert 0 <= row.pass_share <= 1 and row.contribution < row.gross
    assert all(cs[y].R >= 0 and cs[y].retained <= cs[y - 1].R for y in range(1, 4)), "cannot retain more than last year's repeaters"
    c_single, c_pass = contribution(a)
    assert c_pass < c_single and contribution(a, include_fee=False)[1] > c_pass
    caps = {c.name: c.holds_until for c in capacity(a)}
    assert caps["Parking"] > 0 and caps["Gates"] > caps["Parking"] * 0 and caps["Not assessed"] is None
    months = [simulate(x, a)[0] for x in a.incremental_rows]
    for lo, hi in zip(months, months[1:]):
        assert lo is None or (hi is not None and hi <= lo), "more incremental visits cannot pay back later"
    assert simulate(0, a)[0] is None, "savings alone must never pay back"
    ramp = [attribution_ramp(mo, a) for mo in range(1, a.horizon_months + 1)]
    assert ramp == sorted(ramp) and ramp[a.attribution_start_month - 1] == 0 and ramp[-1] == 1.0
    cost = [simulate(0, a)[1]]
    assert all(x >= 0 for x in cost)
    text, missing = replace_blocks(render_all(a), a)
    assert not missing and text == render_all(a), "table generation must be idempotent"


def self_test(a: Assumptions = A) -> None:
    # hand-computable anchors
    assert round(weekend_day(5_000, 0.35)) == 9_333
    assert round(weekend_day(15_000, 0.60)) == 21_000
    assert opex(1_500_000, a) == 827_500
    assert round(contribution(a)[0], 2) == 16.85 and round(contribution(a)[1], 2) == 10.85
    assert round(contribution(a, include_fee=False)[0], 2) == 17.0 and round(contribution(a, include_fee=False)[1], 2) == 11.0
    assert capacity(a)[0].holds_until == 15_000
    assert [round(v) for v in yearly_volume(a)] == [1_500_000, 1_725_000, 2_400_000, 3_675_000]
    assert round(cohorts(a)[0].H) == 357_143 and round(cohorts(a)[0].R) == 35_714
    # invariants under three assumption sets
    for alt in (a, PESSIMISTIC, OPTIMISTIC):
        invariants(alt)
    assert payback_window(a) is not None
    print("self-test OK (anchors + invariants on 3 assumption sets)")


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
        print("business case: tables and cross-referenced numbers match the model")
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
