"""
Chess-style Elo rating system adapted for UFC fighters.

Ratings are computed chronologically: for every fight we record each fighter's
PRE-fight rating (the leakage-safe feature), then update both ratings AFTER the
result is known. A global rating is used (not per-division) so it handles
fighters who change weight classes (e.g. Pereira MW->LHW->HW, Topuria FW->LW).
"""

BASE_RATING = 1500.0
K_FACTOR = 40.0          # higher than chess (32): fighters have few bouts, ratings must move
FINISH_BONUS = 1.10      # KO/Sub wins move Elo 10% more than decisions (dominance signal)


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that A beats B under the Elo model."""
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def update(rating_a: float, rating_b: float, score_a: float, k: float = K_FACTOR):
    """Return updated (rating_a, rating_b). score_a: 1=A win, 0.5=draw, 0=A loss."""
    exp_a = expected_score(rating_a, rating_b)
    new_a = rating_a + k * (score_a - exp_a)
    new_b = rating_b + k * ((1.0 - score_a) - (1.0 - exp_a))
    return new_a, new_b


def run_elo(fights):
    """
    fights: list of dicts sorted chronologically, each with keys
            red, blue, outcome ('red_win'|'blue_win'|'draw'|...), is_finish (bool)
    Mutates each dict in place, adding: red_elo_pre, blue_elo_pre, elo_diff.
    Returns the final {fighter: rating} dict.
    """
    ratings = {}
    for f in fights:
        r = ratings.get(f["red"], BASE_RATING)
        b = ratings.get(f["blue"], BASE_RATING)
        f["red_elo_pre"] = r
        f["blue_elo_pre"] = b
        f["elo_diff"] = r - b

        if f["outcome"] == "red_win":
            score_r = 1.0
        elif f["outcome"] == "blue_win":
            score_r = 0.0
        elif f["outcome"] == "draw":
            score_r = 0.5
        else:
            # no_contest / overturned: skip the update, ratings unchanged
            continue

        k = K_FACTOR * (FINISH_BONUS if f.get("is_finish") else 1.0)
        ratings[f["red"]], ratings[f["blue"]] = update(r, b, score_r, k)
    return ratings
