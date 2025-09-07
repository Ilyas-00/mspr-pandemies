# tests/conftest.py
import sys
from pathlib import Path

# 🔧 Ajouter la racine du projet au PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestRegressor

# ⚠️ importer le MODULE pour pouvoir monkeypatcher ses variables
import api.ml_router as ml


@pytest.fixture()
def tmp_model_and_features(tmp_path: Path):
    """Crée un modèle .pkl et un features_data.csv de test, retourne leurs chemins."""
    feature_cols = [
        "population",
        "nouveaux_cas",
        "nouveaux_cas_j-1",
        "taux_transmission_j-1",
        "moyenne_7j_nouveaux_cas",
        "moyenne_7j_taux",
    ]
    target_col = "taux_transmission"

    # --- Jeu d'entraînement synthétique ---
    rng = np.random.default_rng(0)
    X = rng.uniform(low=0, high=1000, size=(50, len(feature_cols)))
    y = rng.uniform(low=0, high=0.01, size=50)

    # 👉 fit avec des noms de colonnes (supprime le warning sklearn)
    X_df = pd.DataFrame(X, columns=feature_cols)
    model = RandomForestRegressor(n_estimators=10, random_state=0)
    model.fit(X_df, y)

    model_path = tmp_path / "model_taux_transmission_rf.pkl"
    joblib.dump(model, model_path)

    # --- features_data.csv de test (France/Spain, avec NaN pour tester JSON-safe) ---
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    base = pd.DataFrame({
        "date_stat": np.tile(dates, 2),
        "nom_pays": ["France"] * 10 + ["Spain"] * 10,
        "population": 1_000_000,
        "nouveaux_cas": rng.uniform(0, 500, 20),
        "nouveaux_cas_j-1": rng.uniform(0, 500, 20),
        "taux_transmission_j-1": rng.uniform(0, 0.01, 20),
        "moyenne_7j_nouveaux_cas": rng.uniform(0, 500, 20),
        "moyenne_7j_taux": rng.uniform(0, 0.01, 20),
        target_col: rng.uniform(0, 0.01, 20),
    })
    # NaN sur Spain pour vérifier que l'API renvoie null (et pas NaN) en JSON
    base.loc[base["nom_pays"] == "Spain", target_col] = np.nan

    features_csv = tmp_path / "features_data.csv"
    base.to_csv(features_csv, index=False)

    return {
        "model_path": model_path,
        "features_csv": features_csv,
        "feature_cols": feature_cols,
        "target_col": target_col,
    }


@pytest.fixture()
def test_client(tmp_model_and_features):
    """FastAPI minimal avec le router ML, patché pour utiliser les fichiers temporaires."""
    # reset / rediriger vers les artefacts temporaires
    ml._model = None
    ml.MODEL_PATH = tmp_model_and_features["model_path"]
    ml.FEATURES_CSV = tmp_model_and_features["features_csv"]

    app = FastAPI()
    app.include_router(ml.router)
    return TestClient(app)


# --- Hooks pytest pour afficher START / PASS / FAIL / SKIPPED ---
def pytest_runtest_logstart(nodeid, location):
    print(f"\n▶ START: {nodeid}")

def pytest_runtest_logreport(report):
    if report.when == "call":
        if report.passed:
            print(f"✔ PASS: {report.nodeid}")
        elif report.failed:
            print(f"✖ FAIL: {report.nodeid}")
        elif report.skipped:
            print(f"⚠ SKIPPED: {report.nodeid}")
