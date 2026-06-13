"""
Feature engineering for UFC fight prediction.

ONE code path builds features for both training and inference, to avoid
train/serve skew (the main flaw in the World Cup reference project).

Leakage rule: every feature for a fight must be knowable BEFORE that fight.
- Per-fighter performance stats are rolling/career aggregates over PRIOR fights
  only (built by walking history in order and recording state *before* each bout).
- Elo is the pre-fight rating (see elo.py).
- Physical attributes (reach, height, stance) are static; age is computed at the
  fight date; layoff is days since the fighter's previous bout.
"""
import re
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import elo as elo_mod

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MERGED = RAW / "fights.csv"                 # per-fight stats (red/blue corners)
FIGHTER_DETAILS = RAW / "fighter_details.csv"   # static physicals (height/reach/stance/DOB)


# ----------------------------- parsing helpers -----------------------------
def parse_landed(x):
    """'27 of 35' -> (27, 35); '---' / '' -> (nan, nan)."""
    if not isinstance(x, str) or "of" not in x:
        return (np.nan, np.nan)
    a, b = x.split("of")
    try:
        return (float(a.strip()), float(b.strip()))
    except ValueError:
        return (np.nan, np.nan)


def ctrl_to_sec(x):
    """'3:57' -> 237.0 ; '' -> nan."""
    if not isinstance(x, str) or ":" not in x:
        return np.nan
    m, s = x.split(":")
    try:
        return float(m) * 60 + float(s)
    except ValueError:
        return np.nan


def height_to_in(x):
    """\"5' 11\\\"\" -> 71.0"""
    if not isinstance(x, str):
        return np.nan
    m = re.match(r"(\d+)'\s*(\d+)", x)
    return float(m.group(1)) * 12 + float(m.group(2)) if m else np.nan


def reach_to_in(x):
    if not isinstance(x, str):
        return np.nan
    m = re.match(r"(\d+)", x)
    return float(m.group(1)) if m else np.nan


def is_finish(method):
    return isinstance(method, str) and ("KO/TKO" in method or "Submission" in method)


def method_class(method):
    """Collapse to KO/TKO, Submission, Decision, Other."""
    if not isinstance(method, str):
        return "Other"
    if "KO/TKO" in method or method.startswith("TKO"):
        return "KO/TKO"
    if "Submission" in method:
        return "Submission"
    if "Decision" in method:
        return "Decision"
    return "Other"


# ----------------------------- load + clean -----------------------------
def load_fights():
    """Return a chronological DataFrame, one row per fight, with parsed fields."""
    df = pd.read_csv(MERGED, dtype=str).fillna("")
    df["date"] = pd.to_datetime(df["event_date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # parse stat strings into numeric landed/attempted
    for corner in ("red", "blue"):
        for stat in ("sig_str", "total_str", "TD"):
            ld, at = zip(*df[f"{corner}_fighter_{stat}"].map(parse_landed))
            df[f"{corner}_{stat}_l"] = ld
            df[f"{corner}_{stat}_a"] = at
        df[f"{corner}_kd"] = pd.to_numeric(df[f"{corner}_fighter_KD"], errors="coerce")
        df[f"{corner}_sub_att"] = pd.to_numeric(df[f"{corner}_fighter_sub_att"], errors="coerce")
        df[f"{corner}_ctrl"] = df[f"{corner}_fighter_ctrl"].map(ctrl_to_sec)

    df["is_finish"] = df["method"].map(is_finish)
    df["method_class"] = df["method"].map(method_class)
    df["fight_sec"] = (pd.to_numeric(df["round"], errors="coerce") - 1) * 300 + \
        df["time"].map(ctrl_to_sec).fillna(0)
    return df


def load_physicals():
    """fighter (UPPER) -> dict(height_in, reach_in, stance, dob)."""
    fd = pd.read_csv(FIGHTER_DETAILS, dtype=str).fillna("")
    out = {}
    for _, r in fd.iterrows():
        out[r["fighter_name"].strip().upper()] = {
            "height_in": height_to_in(r["Height"]),
            "reach_in": reach_to_in(r["Reach"]),
            "stance": r["Stance"].strip() or "Orthodox",
            "dob": pd.to_datetime(r["DOB"], errors="coerce"),
        }
    return out


# ----------------------------- per-fighter history -----------------------------
def fighter_bout_log(df):
    """
    Explode each fight into two fighter-perspective rows (the fighter + opponent
    stats), chronological. Used to compute pre-fight rolling aggregates.
    """
    recs = []
    for _, f in df.iterrows():
        for me, opp in (("red", "blue"), ("blue", "red")):
            won = (f["fight_outcome"] == f"{me}_win")
            recs.append({
                "fighter": f[f"{me}_fighter_name"],
                "date": f["date"],
                "won": int(won),
                "is_finish_win": int(won and f["is_finish"]),
                "is_finish_loss": int((not won) and f["is_finish"] and f["fight_outcome"] in ("red_win", "blue_win")),
                "decided": int(f["fight_outcome"] in ("red_win", "blue_win", "draw")),
                "sig_l": f[f"{me}_sig_str_l"],
                "sig_a": f[f"{me}_sig_str_a"],
                "sig_absorbed": f[f"{opp}_sig_str_l"],
                "td_l": f[f"{me}_TD_l"],
                "td_a": f[f"{me}_TD_a"],
                "td_against": f[f"{opp}_TD_l"],
                "kd": f[f"{me}_kd"],
                "kd_against": f[f"{opp}_kd"],
                "sub_att": f[f"{me}_sub_att"],
                "ctrl": f[f"{me}_ctrl"],
                "method_class": f["method_class"] if won else "loss",
            })
    log = pd.DataFrame(recs).sort_values("date").reset_index(drop=True)
    return log


def _safe(n, d):
    return n / d if d else np.nan


def pre_fight_state(group):
    """
    Given one fighter's chronological bout log, return a list of pre-fight state
    dicts (state BEFORE each bout). Index-aligned with the group's rows.
    """
    states = []
    n = 0
    wins = 0
    fin_wins = 0
    sig_l = sig_a = sig_abs = td_l = td_a = td_against = kd = sub = ctrl = 0.0
    last5 = []          # recent results
    last_date = None
    for _, r in group.iterrows():
        # ---- emit state BEFORE this bout ----
        states.append({
            "n_fights": n,
            "win_rate": _safe(wins, n),
            "finish_rate": _safe(fin_wins, n),
            "recent_win_rate": _safe(sum(last5), len(last5)) if last5 else np.nan,
            "streak": _current_streak(last5),
            "avg_sig_landed": _safe(sig_l, n),
            "avg_sig_absorbed": _safe(sig_abs, n),
            "sig_acc": _safe(sig_l, sig_a),
            "avg_td_landed": _safe(td_l, n),
            "td_acc": _safe(td_l, td_a),
            "avg_td_against": _safe(td_against, n),
            "avg_kd": _safe(kd, n),
            "avg_sub_att": _safe(sub, n),
            "avg_ctrl": _safe(ctrl, n),
            "days_since_last": (r["date"] - last_date).days if last_date is not None else np.nan,
        })
        # ---- fold this bout into running state ----
        n += 1
        wins += r["won"]
        fin_wins += r["is_finish_win"]
        sig_l += _nz(r["sig_l"]); sig_a += _nz(r["sig_a"]); sig_abs += _nz(r["sig_absorbed"])
        td_l += _nz(r["td_l"]); td_a += _nz(r["td_a"]); td_against += _nz(r["td_against"])
        kd += _nz(r["kd"]); sub += _nz(r["sub_att"]); ctrl += _nz(r["ctrl"])
        last5 = (last5 + [r["won"]])[-5:]
        last_date = r["date"]
    return states


STANCE_RANK = {"Orthodox": 0, "Southpaw": 1, "Switch": 2, "Open Stance": 3, "Sideways": 4}


def _d(a, b, key):
    """red - blue differential for a state key; nan if either missing."""
    va, vb = a.get(key), b.get(key)
    if va is None or vb is None or _isnan(va) or _isnan(vb):
        return np.nan
    return va - vb


def _sub(a, b):
    if a is None or b is None or _isnan(a) or _isnan(b):
        return np.nan
    return a - b


def _isnan(x):
    return isinstance(x, float) and math.isnan(x)


def _age(phys, date):
    dob = phys.get("dob")
    return (date - dob).days / 365.25 if dob is not None and pd.notna(dob) else np.nan


def build_feature_vector(elo_red, elo_blue, rs, bs, rp, bp, date):
    """The single source of truth for a fight's 22-feature vector.
    rs/bs: red/blue pre-fight state dicts; rp/bp: physical dicts; date: fight date.
    Used identically at training (build_dataset) and inference (predict)."""
    return {
        "elo_diff": elo_red - elo_blue, "elo_red": elo_red, "elo_blue": elo_blue,
        "win_rate_diff": _d(rs, bs, "win_rate"),
        "recent_win_rate_diff": _d(rs, bs, "recent_win_rate"),
        "finish_rate_diff": _d(rs, bs, "finish_rate"),
        "streak_diff": _d(rs, bs, "streak"),
        "sig_landed_diff": _d(rs, bs, "avg_sig_landed"),
        "sig_absorbed_diff": _d(rs, bs, "avg_sig_absorbed"),
        "sig_acc_diff": _d(rs, bs, "sig_acc"),
        "td_landed_diff": _d(rs, bs, "avg_td_landed"),
        "td_acc_diff": _d(rs, bs, "td_acc"),
        "td_against_diff": _d(rs, bs, "avg_td_against"),
        "kd_diff": _d(rs, bs, "avg_kd"),
        "sub_att_diff": _d(rs, bs, "avg_sub_att"),
        "ctrl_diff": _d(rs, bs, "avg_ctrl"),
        "reach_diff": _sub(rp.get("reach_in"), bp.get("reach_in")),
        "height_diff": _sub(rp.get("height_in"), bp.get("height_in")),
        "age_diff": _sub(_age(rp, date), _age(bp, date)),
        "layoff_diff": _d(rs, bs, "days_since_last"),
        "exp_diff": _d(rs, bs, "n_fights"),
        "stance_diff": int(STANCE_RANK.get(rp.get("stance"), 0) != STANCE_RANK.get(bp.get("stance"), 0)),
    }


def _nz(x):
    return 0.0 if (x is None or (isinstance(x, float) and math.isnan(x))) else float(x)


def _current_streak(results):
    """+k win streak / -k loss streak over the trailing results list."""
    if not results:
        return 0
    s = 0
    last = results[-1]
    for r in reversed(results):
        if r == last:
            s += 1
        else:
            break
    return s if last == 1 else -s
