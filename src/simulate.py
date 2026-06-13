"""
Monte Carlo simulation of the full card.

Each fight is a Bernoulli draw on the model's P(red win). For a single fight MC
just reproduces the model probability, so the value here is CARD-LEVEL structure:
  - distribution of how many favorites win (0..7)
  - probability the whole card goes chalk (all favorites win) + parlay odds
  - the most likely exact result combination
  - 95% interval on "favorites correct"
N=10,000 (each sim is 7 coin flips; runtime is milliseconds, SE ~0.5%).
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
N_SIMS = 10_000
SEED = 42


def main():
    data = json.load(open(OUT / "predictions.json"))
    fights = data["fights"]
    fav_probs = np.array([f["fav_prob"] for f in fights])   # each >= 0.5
    n = len(fights)

    rng = np.random.default_rng(SEED)
    # sim[s, i] = 1 if favorite of fight i wins in sim s
    draws = rng.random((N_SIMS, n)) < fav_probs
    fav_wins_per_sim = draws.sum(axis=1)

    # distribution of number of favorites winning
    dist = np.bincount(fav_wins_per_sim, minlength=n + 1) / N_SIMS

    # exact-combination mode
    combos, counts = np.unique(draws, axis=0, return_counts=True)
    top = np.argsort(-counts)[:5]
    likely_combos = []
    for t in top:
        combo = combos[t]
        likely_combos.append({
            "winners": [f["favorite"] if combo[i] else (f["blue"] if f["favorite"] == f["red"] else f["red"])
                        for i, f in enumerate(fights)],
            "n_upsets": int((~combo).sum()),
            "prob": round(counts[t] / N_SIMS, 4),
        })

    chalk_sim = float((fav_wins_per_sim == n).mean())
    chalk_analytic = float(np.prod(fav_probs))
    lo, hi = np.percentile(fav_wins_per_sim, [2.5, 97.5])

    sim = {
        "n_sims": N_SIMS,
        "fav_wins_distribution": {str(k): round(float(dist[k]), 4) for k in range(n + 1)},
        "expected_favorites_correct": round(float(fav_wins_per_sim.mean()), 3),
        "favorites_correct_95ci": [int(lo), int(hi)],
        "all_chalk_prob": round(chalk_sim, 4),
        "all_chalk_parlay_decimal_odds": round(1 / chalk_analytic, 1) if chalk_analytic > 0 else None,
        "expected_upsets": round(float(n - fav_wins_per_sim.mean()), 3),
        "most_likely_outcomes": likely_combos,
    }
    data["simulation"] = sim
    with open(OUT / "predictions.json", "w") as fh:
        json.dump(data, fh, indent=2)

    print(f"Monte Carlo: {N_SIMS:,} sims over {n} fights")
    print(f"  Expected favorites correct : {sim['expected_favorites_correct']} / {n}  "
          f"(95% CI {sim['favorites_correct_95ci']})")
    print(f"  All-chalk (every favorite wins): {sim['all_chalk_prob']*100:.1f}%  "
          f"(parlay ~{sim['all_chalk_parlay_decimal_odds']}x)")
    print(f"  Expected upsets            : {sim['expected_upsets']}")
    print("  Favorites-correct distribution:")
    for k in range(n + 1):
        bar = "#" * int(dist[k] * 80)
        print(f"    {k}/{n}: {dist[k]*100:5.1f}% {bar}")
    print(f"  Most likely card result ({likely_combos[0]['prob']*100:.1f}%, "
          f"{likely_combos[0]['n_upsets']} upsets)")
    print(f"\n-> updated {OUT/'predictions.json'}")


if __name__ == "__main__":
    main()
