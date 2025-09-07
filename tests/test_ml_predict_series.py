# tests/test_ml_predict_series.py
import pytest
import api.ml_router as ml  # pour monkeypatch dans certains tests

def test_available_countries_ok(test_client):
    r = test_client.get("/ml/available_countries")
    assert r.status_code == 200
    data = r.json()
    assert "countries" in data and isinstance(data["countries"], list)
    # La fixture crée France et Spain
    assert "France" in data["countries"]
    assert "Spain" in data["countries"]

def test_predict_series_france_ok_jsonsafe(test_client):
    r = test_client.get("/ml/predict_series/France")
    assert r.status_code == 200
    payload = r.json()
    assert payload["nom_pays"] == "France"
    pts = payload["points"]
    assert isinstance(pts, list) and len(pts) > 0
    # JSON-safe : pas de NaN/Inf -> soit float, soit None
    for p in pts:
        assert "date" in p
        assert "taux_true" in p and "taux_pred" in p
        assert (p["taux_true"] is None) or isinstance(p["taux_true"], float)
        assert (p["taux_pred"] is None) or isinstance(p["taux_pred"], float)

def test_predict_series_spain_contains_nulls_for_nan(test_client):
    # Spain a des NaN dans la cible (conftest) -> doivent devenir null en JSON
    r = test_client.get("/ml/predict_series/Spain")
    assert r.status_code == 200
    pts = r.json()["points"]
    assert any(p["taux_true"] is None for p in pts)

def test_predict_series_unknown_country_404(test_client):
    r = test_client.get("/ml/predict_series/Narnia")
    assert r.status_code == 404

def test_available_countries_503_when_features_missing(test_client, tmp_path):
    # Simule features.csv manquant
    ml.FEATURES_CSV = tmp_path / "no_features.csv"
    r = test_client.get("/ml/available_countries")
    assert r.status_code == 503

def test_predict_series_503_when_model_missing(test_client, tmp_path):
    # Simule modèle manquant
    ml._model = None
    ml.MODEL_PATH = tmp_path / "no_model.pkl"
    r = test_client.get("/ml/predict_series/France")
    assert r.status_code == 503
