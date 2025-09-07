# tests/test_api_smoke.py
import os
import json
import importlib
from pathlib import Path
import pandas as pd
from joblib import dump
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestRegressor

def make_tiny_dataset(tmp: Path):
    # colonnes features de ton config actuel
    feature_cols = [
        "population",
        "nouveaux_cas",
        "nouveaux_cas_j-1",
        "taux_transmission_j-1",
        "moyenne_7j_nouveaux_cas",
        "moyenne_7j_taux",
    ]
    target_col = "taux_transmission"

    # 10 lignes factices pour "France"
    n = 10
    df = pd.DataFrame({
        "nom_pays": ["France"] * n,
        "date_stat": pd.date_range("2022-01-01", periods=n, freq="D"),
        "population": [67_000_000] * n,
        "nouveaux_cas": list(range(10, 10 + n)),
        "nouveaux_cas_j-1": list(range(9, 9 + n)),
        "taux_transmission_j-1": [1.0 + i*0.01 for i in range(n)],
        "moyenne_7j_nouveaux_cas": [15.0] * n,
        "moyenne_7j_taux": [1.05] * n,
        target_col: [1.1 + i*0.01 for i in range(n)],
    })
    return df, feature_cols, target_col

def test_api_ml_endpoints(tmp_path, monkeypatch):
    # 1) Prépare fichiers temporaires
    features_csv = tmp_path / "features_data.csv"
    model_path   = tmp_path / "model.pkl"

    df, feature_cols, target_col = make_tiny_dataset(tmp_path)
    df.to_csv(features_csv, index=False)

    # 2) Modèle minuscule (entraîné sur les features factices)
    X = df[feature_cols]
    y = df[target_col]
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(X, y)
    dump(model, model_path)

    # 3) Patcher l'environnement pour que l'API lise nos chemins
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("FEATURES_CSV", str(features_csv))
    monkeypatch.setenv("CLEAN_DATA_CSV", str(tmp_path / "clean.csv"))
    monkeypatch.setenv("PREDICTIONS_CSV", str(tmp_path / "preds.csv"))
    monkeypatch.setenv("MALADIE_CIBLE", "covid_19")

    # 4) Recharger les modules de config/route pour prendre en compte les env vars
    import prediction.config as config
    importlib.reload(config)
    import api.ml_router as ml_router
    importlib.reload(ml_router)
    import api.api_pandemies as api_pandemies
    importlib.reload(api_pandemies)

    # 5) Client FastAPI
    app = api_pandemies.app
    client = TestClient(app)

    # 6) /ml/available_countries
    r = client.get("/ml/available_countries")
    assert r.status_code == 200
    data = r.json()
    assert "countries" in data and "France" in data["countries"]

    # 7) /ml/predict_series/France
    r = client.get("/ml/predict_series/France")
    assert r.status_code == 200
    serie = r.json()
    assert serie["nom_pays"].lower() == "france"
    assert len(serie["points"]) > 0

    # JSON-safe: pas de NaN/Inf → None ou float
    pt0 = serie["points"][0]
    assert "date" in pt0 and "taux_true" in pt0 and "taux_pred" in pt0
    assert (pt0["taux_true"] is None) or isinstance(pt0["taux_true"], float)
    assert (pt0["taux_pred"] is None) or isinstance(pt0["taux_pred"], float)

def test_docs_available():
    # vérifie que la doc Swagger répond
    from api.api_pandemies import app
    client = TestClient(app)
    r = client.get("/docs")
    assert r.status_code == 200
    assert "Swagger UI" in r.text
