"""
Build the model-ready feature matrix from the raw fight dataset (data/raw/).

Pipeline: load+clean -> Elo (pre-fight) -> per-fighter rolling pre-fight state
-> physical/contextual features -> differentials -> feature_matrix.csv
Also writes fighter_state.json: each fighter's latest post-history state + final
Elo, consumed at inference time so the card uses the identical feature path.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import elo as elo_mod
import features as F

OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)

# feature columns fed to the win model (differentials = red - blue unless noted)
FEATURE_COLS = [
    "elo_diff", "elo_red", "elo_blue",
    "win_rate_diff", "recent_win_rate_diff", "finish_rate_diff", "streak_diff",
    "sig_landed_diff", "sig_absorbed_diff", "sig_acc_diff",
    "td_landed_diff", "td_acc_diff", "td_against_diff",
    "kd_diff", "sub_att_diff", "ctrl_diff",
    "reach_diff", "height_diff", "age_diff", "layoff_diff",
    "exp_diff", "stance_diff",
]


def main():
    df = F.load_fights()
    phys = F.load_physicals()

    # ---- Elo over full chronology ----
    fights = [{"red": r["red_fighter_name"], "blue": r["blue_fighter_name"],
               "outcome": r["fight_outcome"], "is_finish": bool(r["is_finish"])}
              for _, r in df.iterrows()]
    final_elo = elo_mod.run_elo(fights)
    df["elo_red"] = [f["red_elo_pre"] for f in fights]
    df["elo_blue"] = [f["blue_elo_pre"] for f in fights]
    df["elo_diff"] = [f["elo_diff"] for f in fights]

    # ---- per-fighter rolling pre-fight state ----
    log = F.fighter_bout_log(df)
    log_state = {}                       # (fighter, idx_in_group) -> state
    latest_state = {}                    # fighter -> last post-history state for inference
    state_rows = []
    for fighter, g in log.groupby("fighter", sort=False):
        g = g.sort_values("date")
        states = F.pre_fight_state(g)
        for (idx, _), st in zip(g.iterrows(), states):
            log_state[idx] = st
        # build the "after all fights" state for inference (fold the last bout in too)
        latest_state[fighter] = _final_state(g, states)

    # attach state back onto the wide fight table by re-deriving per corner.
    # We rebuild per-corner state by replaying: simplest is to map via the log order.
    red_state, blue_state = _map_states_to_fights(df, log, log_state)

    feat = _assemble(df, red_state, blue_state, phys)
    feat.to_csv(OUT / "feature_matrix.csv", index=False)

    # inference artifact
    inf = {"final_elo": final_elo,
           "fighter_state": {k: _jsonable(v) for k, v in latest_state.items()},
           "physicals": {k: _jsonable_phys(v) for k, v in phys.items()},
           "feature_cols": FEATURE_COLS}
    with open(OUT / "fighter_state.json", "w") as fh:
        json.dump(inf, fh)

    print(f"feature_matrix: {len(feat):,} rows x {len(FEATURE_COLS)} features -> {OUT/'feature_matrix.csv'}")
    print(f"target balance:\n{feat['target'].value_counts(normalize=True).round(3)}")
    print(f"null fraction per feature (top):")
    print(feat[FEATURE_COLS].isna().mean().sort_values(ascending=False).head(8).round(3))
    print(f"fighters with state: {len(latest_state):,}")


def _final_state(g, states):
    """State AFTER all of a fighter's fights (for inference). Reuse pre_fight_state by
    appending a sentinel: simplest is to recompute by folding everything."""
    # fold all bouts -> emulate pre_fight_state's accumulation one past the end
    n = len(g)
    wins = int(g["won"].sum())
    fin_wins = int(g["is_finish_win"].sum())
    last5 = list(g["won"])[-5:]
    sums = {c: float(np.nansum(g[c].astype(float))) for c in
            ["sig_l", "sig_a", "sig_absorbed", "td_l", "td_a", "td_against", "kd", "sub_att", "ctrl"]}
    last_date = g["date"].max()
    return {
        "n_fights": n,
        "win_rate": F._safe(wins, n),
        "finish_rate": F._safe(fin_wins, n),
        "recent_win_rate": F._safe(sum(last5), len(last5)) if last5 else np.nan,
        "streak": F._current_streak(last5),
        "avg_sig_landed": F._safe(sums["sig_l"], n),
        "avg_sig_absorbed": F._safe(sums["sig_absorbed"], n),
        "sig_acc": F._safe(sums["sig_l"], sums["sig_a"]),
        "avg_td_landed": F._safe(sums["td_l"], n),
        "td_acc": F._safe(sums["td_l"], sums["td_a"]),
        "avg_td_against": F._safe(sums["td_against"], n),
        "avg_kd": F._safe(sums["kd"], n),
        "avg_sub_att": F._safe(sums["sub_att"], n),
        "avg_ctrl": F._safe(sums["ctrl"], n),
        "days_since_last": None,            # filled at inference from the card date
        "last_date": str(last_date.date()) if pd.notna(last_date) else None,
    }


def _map_states_to_fights(df, log, log_state):
    """For each wide fight row, recover the pre-fight state of red & blue.
    log rows were emitted in (fight order x [red, blue]); reconstruct by walking."""
    red_state, blue_state = [], []
    # walk each fighter's states in chronological order; df is also date-sorted,
    # so popping in order aligns red/blue state with each wide fight row.
    from collections import defaultdict
    cursor = defaultdict(int)
    per_fighter_states = defaultdict(list)
    for idx, row in log.sort_values("date").iterrows():
        per_fighter_states[row["fighter"]].append(log_state[idx])
    for _, f in df.iterrows():
        r = f["red_fighter_name"]; b = f["blue_fighter_name"]
        red_state.append(per_fighter_states[r][cursor[r]]); cursor[r] += 1
        blue_state.append(per_fighter_states[b][cursor[b]]); cursor[b] += 1
    return red_state, blue_state


def _assemble(df, red_state, blue_state, phys):
    rows = []
    for i, (_, f) in enumerate(df.iterrows()):
        rs, bs = red_state[i], blue_state[i]
        rp = phys.get(f["red_fighter_name"], {})
        bp = phys.get(f["blue_fighter_name"], {})
        rec = {
            "date": f["date"], "red": f["red_fighter_name"], "blue": f["blue_fighter_name"],
            "bout_type": f["bout_type"], "method_class": f["method_class"],
            "round": f["round"], "outcome": f["fight_outcome"],
        }
        rec.update(F.build_feature_vector(f["elo_red"], f["elo_blue"], rs, bs, rp, bp, f["date"]))
        rec["target"] = 1 if f["fight_outcome"] == "red_win" else (0 if f["fight_outcome"] == "blue_win" else np.nan)
        rows.append(rec)
    out = pd.DataFrame(rows)
    out = out.dropna(subset=["target"]).reset_index(drop=True)   # binary: drop draw/NC
    out["target"] = out["target"].astype(int)
    return out


def _jsonable(st):
    return {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in st.items()}


def _jsonable_phys(p):
    return {"height_in": _n(p.get("height_in")), "reach_in": _n(p.get("reach_in")),
            "stance": p.get("stance"),
            "dob": str(p["dob"].date()) if p.get("dob") is not None and pd.notna(p.get("dob")) else None}


def _n(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)


if __name__ == "__main__":
    main()
