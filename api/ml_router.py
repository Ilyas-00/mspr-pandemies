# api/ml_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field  # (utile si tu gardes /ml/predict unitaire)
from joblib import load
from pathlib import Path
import math
import pandas as pd

from prediction.config import MODEL_PATH, FEATURE_COLS, FEATURES_CSV, TARGET_COL

router = APIRouter(prefix="/ml", tags=["ML"])
_model = None  # lazy-load


def get_model():
    global _model
    if _model is None:
        if not Path(MODEL_PATH).exists():
            raise HTTPException(status_code=503, detail="Modèle introuvable. Entraînez-le d'abord.")
        _model = load(MODEL_PATH)
    return _model


# --- util: normaliser les noms pays (espaces/underscores, casse) ---
def _norm(s: str) -> str:
    return str(s).strip().lower().replace(" ", "_")


@router.get("/available_countries")
def available_countries():
    if not Path(FEATURES_CSV).exists():
        raise HTTPException(status_code=503, detail="features_data.csv introuvable.")
    df = pd.read_csv(FEATURES_CSV)
    pays = sorted(set(p for p in df["nom_pays"].dropna().astype(str)))
    return {"countries": pays}


@router.get("/predict_series/{nom_pays}")
def predict_series(nom_pays: str):
    model = get_model()

    if not Path(FEATURES_CSV).exists():
        raise HTTPException(status_code=503, detail="features_data.csv introuvable. Lance l'étape features.")
    try:
        df = pd.read_csv(FEATURES_CSV, parse_dates=["date_stat"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lecture features_data.csv impossible: {e}")

    # Accepter 'United States' ou 'United_States', 'france' ou 'France', etc.
    mask = df["nom_pays"].astype(str).apply(_norm) == _norm(nom_pays)
    d = df[mask].copy()
    if d.empty:
        raise HTTPException(status_code=404, detail=f"Aucune donnée pour {nom_pays} dans features_data.csv")

    # PRÉDICTION dans l'ordre exact des features d'entraînement
    try:
        y_pred = model.predict(d[FEATURE_COLS])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur modèle: {e}")

    d["taux_pred"] = pd.Series(y_pred)

    # --- SANITISATION pour JSON ---
    # 1) Forcer numérique et remplacer non-fini (NaN/Inf) par None dans la réponse
    if TARGET_COL in d.columns:
        d[TARGET_COL] = pd.to_numeric(d[TARGET_COL], errors="coerce")
    else:
        d[TARGET_COL] = pd.NA
    d["taux_pred"] = pd.to_numeric(d["taux_pred"], errors="coerce")

    # 2) Drop les dates NaT (pas sérialisables)
    d = d.dropna(subset=["date_stat"]).sort_values("date_stat")

    # 3) Helper JSON-safe
    def safe_num(x):
        try:
            xf = float(x)
            return xf if math.isfinite(xf) else None
        except Exception:
            return None

    # 4) Construire la réponse en remplaçant NaN/Inf par None
    points = [
        {
            "date": dt.strftime("%Y-%m-%d"),
            "taux_true": safe_num(t),
            "taux_pred": safe_num(p),
        }
        for dt, t, p in zip(d["date_stat"], d[TARGET_COL], d["taux_pred"])
    ]

    return {"nom_pays": nom_pays, "points": points}
