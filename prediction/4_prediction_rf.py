# prediction/4_prediction_rf.py
import pandas as pd
from joblib import load
from prediction.config import FEATURES_CSV, PREDICTIONS_CSV, MODEL_PATH, FEATURE_COLS, TARGET_COL

def run_predict_batch():
    print("🔮 Inférence batch pour contrôle")
    model = load(MODEL_PATH)
    data = pd.read_csv(FEATURES_CSV, parse_dates=["date_stat"])

    X = data[FEATURE_COLS].copy()
    y_true = data[TARGET_COL].astype(float).values

    y_pred = model.predict(X)

    out = data[["date_stat", "nom_pays", "population"]].copy()
    out["taux_true"] = y_true
    out["taux_pred"] = y_pred
    out["nouveaux_cas_pred"] = (out["taux_pred"] * out["population"]).clip(lower=0)

    out.to_csv(PREDICTIONS_CSV, index=False)
    print(f"✅ Fichier écrit → {PREDICTIONS_CSV.resolve()}  ({len(out):,} lignes)")
    return out

if __name__ == "__main__":
    run_predict_batch()
