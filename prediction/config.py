# prediction/config.py
import os
from pathlib import Path

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", Path(__file__).resolve().parent / "artifacts"))
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Autoriser override via .env / docker
MODEL_PATH = Path(os.getenv("MODEL_PATH", ARTIFACTS_DIR / "model_taux_transmission_rf.pkl"))
CLEAN_DATA_CSV  = Path(os.getenv("CLEAN_DATA_CSV", Path.cwd() / "clean_data.csv"))
FEATURES_CSV    = Path(os.getenv("FEATURES_CSV", Path.cwd() / "features_data.csv"))
PREDICTIONS_CSV = Path(os.getenv("PREDICTIONS_CSV", Path.cwd() / "predictions_resultats_rf.csv"))

MALADIE_CIBLE = os.getenv("MALADIE_CIBLE", "covid_19")

FEATURE_COLS = [
    "population",
    "nouveaux_cas",
    "nouveaux_cas_j-1",
    "taux_transmission_j-1",
    "moyenne_7j_nouveaux_cas",
    "moyenne_7j_taux",
]

TARGET_COL = "taux_transmission"
# prediction/config.py
# from pathlib import Path

# ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
# ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# MODEL_PATH = ARTIFACTS_DIR / "model_taux_transmission_rf.pkl"

# CLEAN_DATA_CSV  = Path.cwd() / "clean_data.csv"
# FEATURES_CSV    = Path.cwd() / "features_data.csv"
# PREDICTIONS_CSV = Path.cwd() / "predictions_resultats_rf.csv"

# MALADIE_CIBLE = "covid_19"

# FEATURE_COLS = [
#     "population",
#     "nouveaux_cas",
#     "nouveaux_cas_j-1",
#     "taux_transmission_j-1",
#     "moyenne_7j_nouveaux_cas",
#     "moyenne_7j_taux",
# ]

# TARGET_COL = "taux_transmission"
