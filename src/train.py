"""
Train and evaluate the fight-prediction model.

Single model by design: XGBoost. On this dataset the algorithm choice is within
noise (we benchmarked Dummy/LogReg/RF/XGBoost — all ~0.60 acc); XGBoost wins on
log-loss/Brier, handles missing values natively (lots of missing reach / debut
fighters), and captures nonlinear interactions (reach×style, age×layoff). So we
keep one model and invest in features + leakage-safety instead.

Also trains a method model (KO/TKO|Submission|Decision) and a finish-round model.
Temporal split: oldest 85% of fights train, most-recent 15% test (never random).
"""
import json
from pathlib import Path

import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"
MODELS.mkdir(exist_ok=True)

with open(DATA / "fighter_state.json") as fh:
    FEATURE_COLS = json.load(fh)["feature_cols"]

# ---------------------------------------------------------------------------
# Feature emphasis: XGBoost uses these as per-feature column-sampling weights
# (higher = offered to splits more often). We push current-form features above
# age so recent results matter a little more than how old a fighter is.
FORM_FEATURES = {"recent_win_rate_diff", "streak_diff", "win_rate_diff", "finish_rate_diff"}
WEIGHT_FORM = 2.8          # vs 1.0 default
WEIGHT_AGE = 0.45          # age_diff specifically — kept in play, just below form
FEATURE_WEIGHTS = [
    WEIGHT_FORM if c in FORM_FEATURES else (WEIGHT_AGE if c == "age_diff" else 1.0)
    for c in FEATURE_COLS
]


def _xgb_win():
    # feature_weights set in the constructor (fit-time is deprecated/ignored);
    # lower colsample_bytree so the weights actually bite on feature selection.
    return XGBClassifier(n_estimators=400, max_depth=3, learning_rate=0.03,
                         subsample=0.8, colsample_bytree=0.45, min_child_weight=5,
                         reg_lambda=2.0, gamma=0.5, eval_metric="logloss",
                         feature_weights=FEATURE_WEIGHTS, importance_type="weight",
                         random_state=42, n_jobs=-1)


def temporal_split(df, frac=0.85):
    df = df.sort_values("date").reset_index(drop=True)
    cut = int(len(df) * frac)
    return df.iloc[:cut], df.iloc[cut:]


def main():
    df = pd.read_csv(DATA / "feature_matrix.csv", parse_dates=["date"])
    train, test = temporal_split(df)
    Xtr, ytr = train[FEATURE_COLS], train["target"]
    Xte, yte = test[FEATURE_COLS], test["target"]
    print(f"train {len(train):,} ({train.date.min().date()}->{train.date.max().date()})  "
          f"test {len(test):,} ({test.date.min().date()}->{test.date.max().date()})")

    # ---- XGBoost win model (handles NaN natively; no imputation needed) ----
    xgb = _xgb_win().fit(Xtr, ytr)
    metrics = _evaluate(xgb, Xte, yte)
    baseline_acc = max(yte.mean(), 1 - yte.mean())   # always-pick-majority reference

    print("\n=== WIN MODEL (XGBoost) — test = most recent 15% ===")
    print(f"  accuracy : {metrics['acc']:.3f}   (always-red baseline {baseline_acc:.3f})")
    print(f"  log loss : {metrics['logloss']:.3f}")
    print(f"  brier    : {metrics['brier']:.3f}")

    fi = sorted(zip(FEATURE_COLS, xgb.feature_importances_), key=lambda x: -x[1])
    print("\nTop 10 features (split frequency):")
    for f, w in fi[:10]:
        print(f"  {w:6.3f}  {f}")

    # ---- method model (multiclass) ----
    method_classes = ["KO/TKO", "Submission", "Decision"]
    mtr = train[train["method_class"].isin(method_classes)]
    mte = test[test["method_class"].isin(method_classes)]
    cls_to_idx = {c: i for i, c in enumerate(method_classes)}
    method_model = XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8, reg_lambda=2.0,
                                 random_state=42, n_jobs=-1)
    method_model.fit(mtr[FEATURE_COLS], mtr["method_class"].map(cls_to_idx))
    macc = accuracy_score(mte["method_class"].map(cls_to_idx),
                          method_model.predict(mte[FEATURE_COLS]))
    print(f"\nMethod model test accuracy: {macc:.3f}  (classes: {method_classes})")

    # ---- finish-round model (KO/Sub only, so it's a real finish round) ----
    fin = ["KO/TKO", "Submission"]
    tr_r = train[train["method_class"].isin(fin)].dropna(subset=["round"]).copy()
    te_r = test[test["method_class"].isin(fin)].dropna(subset=["round"]).copy()
    tr_r["rnd"] = tr_r["round"].astype(int).clip(1, 5)
    te_r["rnd"] = te_r["round"].astype(int).clip(1, 5)
    round_model = XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, reg_lambda=2.0,
                                random_state=42, n_jobs=-1)
    round_model.fit(tr_r[FEATURE_COLS], tr_r["rnd"] - 1)
    racc = accuracy_score(te_r["rnd"] - 1, round_model.predict(te_r[FEATURE_COLS]))
    print(f"Round model (finishes only) test accuracy: {racc:.3f}")

    # ---- persist (refit win model on ALL data for inference) ----
    xgb_full = _xgb_win().fit(df[FEATURE_COLS], df["target"])
    joblib.dump(xgb_full, MODELS / "xgb_win.pkl")
    joblib.dump(method_model, MODELS / "method_model.pkl")
    joblib.dump(round_model, MODELS / "round_model.pkl")
    with open(MODELS / "meta.json", "w") as fh:
        json.dump({"feature_cols": FEATURE_COLS, "method_classes": method_classes,
                   "metrics": metrics, "baseline_acc": float(baseline_acc),
                   "red_prior": float(ytr.mean()), "feature_importance": fi},
                  fh, indent=2, default=float)
    print(f"\nSaved models -> {MODELS}")


def _evaluate(model, X, y):
    p = model.predict_proba(X)[:, 1]
    return {"acc": accuracy_score(y, (p >= 0.5).astype(int)),
            "logloss": log_loss(y, p), "brier": brier_score_loss(y, p)}


if __name__ == "__main__":
    main()
