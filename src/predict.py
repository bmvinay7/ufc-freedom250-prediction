"""
Inference for the UFC Freedom 250 card.

For each of the 7 fights, build the SAME 22-feature vector used in training
(features.build_feature_vector) from each fighter's latest pre-fight state +
Elo + physicals, then predict P(red win) with the single XGBoost model, plus
method (KO/TKO|Submission|Decision) and finish-round distributions.
Writes outputs/predictions.json (consumed by the Monte Carlo + frontend).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

import features as F
import card as CARD

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def load_artifacts():
    state = json.load(open(DATA / "fighter_state.json"))
    meta = json.load(open(MODELS / "meta.json"))
    models = {
        "win": joblib.load(MODELS / "xgb_win.pkl"),
        "method": joblib.load(MODELS / "method_model.pkl"),
        "round": joblib.load(MODELS / "round_model.pkl"),
    }
    return state, meta, models


def fighter_phys(name):
    h, r, stance, dob = CARD.PHYS[name]
    return {"height_in": float(h), "reach_in": float(r), "stance": stance,
            "dob": pd.Timestamp(dob)}


def fighter_state(name, state_json, card_date):
    """Latest pre-fight state, with layoff filled from the card date."""
    st = dict(state_json["fighter_state"].get(name, {}))
    last = st.get("last_date")
    st["days_since_last"] = (card_date - pd.Timestamp(last)).days if last else np.nan
    return st


def confidence_tier(fav_prob):
    if fav_prob >= 0.75:
        return "Heavy Favorite"
    if fav_prob >= 0.65:
        return "Clear Favorite"
    if fav_prob >= 0.55:
        return "Lean"
    return "Pick'em"


def main():
    state, meta, models = load_artifacts()
    fcols = meta["feature_cols"]
    method_classes = meta["method_classes"]
    elo = state["final_elo"]
    card_date = pd.Timestamp(CARD.EVENT["date"])

    rows, feat_rows = [], []
    for red, blue, wc, rounds, billing, title in CARD.FIGHTS:
        rs = fighter_state(red, state, card_date)
        bs = fighter_state(blue, state, card_date)
        rp, bp = fighter_phys(red), fighter_phys(blue)
        fv = F.build_feature_vector(elo.get(red, 1500.0), elo.get(blue, 1500.0),
                                    rs, bs, rp, bp, card_date)
        feat_rows.append(fv)
        rows.append((red, blue, wc, rounds, billing, title))

    X = pd.DataFrame(feat_rows)[fcols]
    p_win = models["win"].predict_proba(X)[:, 1]            # P(red win)
    method_p = models["method"].predict_proba(X)           # (n,3) -> method_classes
    # finish-round model trained on finishes only; align its classes_ into 5 slots
    raw_round = models["round"].predict_proba(X)
    round_p = np.zeros((len(X), 5))
    for col, cls in enumerate(models["round"].classes_):
        round_p[:, int(cls)] = raw_round[:, col]

    fights_out = []
    for i, (red, blue, wc, rounds, billing, title) in enumerate(rows):
        pr = float(p_win[i])
        mp = {method_classes[j]: float(method_p[i][j]) for j in range(len(method_classes))}
        rd = round_p[i][:rounds]
        rd = (rd / rd.sum()).tolist()
        fav_is_red = pr >= 0.5
        fav_prob = pr if fav_is_red else 1 - pr
        elo_r, elo_b = round(elo.get(red, 1500), 1), round(elo.get(blue, 1500), 1)
        fights_out.append({
            "red": CARD.DISPLAY[red], "blue": CARD.DISPLAY[blue],
            "weight_class": wc, "scheduled_rounds": rounds,
            "billing": billing, "title": title,
            "p_red": round(pr, 4), "p_blue": round(1 - pr, 4),
            "elo_red": elo_r, "elo_blue": elo_b,
            "favorite": CARD.DISPLAY[red] if fav_is_red else CARD.DISPLAY[blue],
            "fav_prob": round(fav_prob, 4),
            "confidence": confidence_tier(fav_prob),
            "elo_edge": round(abs(elo_r - elo_b), 1),
            "method_probs": {k: round(v, 4) for k, v in mp.items()},
            "round_probs": [round(x, 4) for x in rd],
            "likely_method": max(mp, key=mp.get),
            "likely_round": int(np.argmax(rd) + 1),
        })

    out = {"event": CARD.EVENT,
           "model": {"name": "XGBoost",
                     "test_accuracy": meta["metrics"]["acc"],
                     "test_logloss": meta["metrics"]["logloss"],
                     "baseline_acc": meta["baseline_acc"]},
           "n_sims": 10000,
           "fights": fights_out}
    with open(OUT / "predictions.json", "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"{'Fight':<34}{'Favorite':<18}{'P(win)':>7}  Outcome")
    print("-" * 80)
    for f in fights_out:
        outcome = (f"Decision ({f['scheduled_rounds']} rds)" if f["likely_method"] == "Decision"
                   else f"{f['likely_method']} R{f['likely_round']}")
        print(f"{f['red']+' vs '+f['blue']:<34}{f['favorite']:<18}{f['fav_prob']*100:>6.1f}%  {outcome}")
    print(f"\n-> {OUT/'predictions.json'}")


if __name__ == "__main__":
    main()
