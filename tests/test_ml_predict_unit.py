# tests/test_ml_predict_unit.py
import pytest

@pytest.mark.parametrize(
    "payload",
    [
        {
            "population": 1_000_000,
            "nouveaux_cas": 120.0,
            "nouveaux_cas_j_1": 110.0,
            "taux_transmission_j_1": 0.0009,
            "moyenne_7j_nouveaux_cas": 115.0,
            "moyenne_7j_taux": 0.0011,
        }
    ],
)
def test_predict_unit_if_available(test_client, payload):
    # Si la route n'existe pas dans ton router actuel, on skip proprement
    resp = test_client.post("/ml/predict", json=payload)
    if resp.status_code == 404:
        pytest.skip("Route /ml/predict absente (OK si non implémentée).")
    assert resp.status_code == 200
    data = resp.json()
    assert "taux_transmission_prédit" in data
    assert isinstance(data["taux_transmission_prédit"], float)
    assert data["taux_transmission_prédit"] >= 0.0
