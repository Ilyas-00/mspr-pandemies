# prediction/2_features_engineering.py
import pandas as pd
from prediction.config import CLEAN_DATA_CSV, FEATURES_CSV, TARGET_COL

ROLL = 7  # fenêtre des moyennes mobiles

def run_features():
    print("🧪 Feature engineering à partir de clean_data.csv")
    df = pd.read_csv(CLEAN_DATA_CSV, parse_dates=["date_stat"])

    # Cible: taux = nouveaux_cas / population
    df[TARGET_COL] = (df["nouveaux_cas"] / df["population"]).clip(lower=0)

    # Groupby pays pour calculer lags et rollings
    df = df.sort_values(["nom_pays", "date_stat"]).copy()
    grp = df.groupby("nom_pays", group_keys=False)

    df["nouveaux_cas_j-1"]      = grp["nouveaux_cas"].shift(1)
    df["taux_transmission_j-1"] = grp[TARGET_COL].shift(1)

    df["moyenne_7j_nouveaux_cas"] = grp["nouveaux_cas"].rolling(ROLL, min_periods=ROLL).mean().reset_index(level=0, drop=True)
    df["moyenne_7j_taux"]         = grp[TARGET_COL].rolling(ROLL, min_periods=ROLL).mean().reset_index(level=0, drop=True)

    # Drop NA (causés par shift/rolling au début des séries)
    before = len(df)
    df = df.dropna(subset=["nouveaux_cas_j-1", "taux_transmission_j-1", "moyenne_7j_nouveaux_cas", "moyenne_7j_taux"])
    after = len(df)
    print(f"🔧 Drop lignes incomplètes: {before - after} lignes supprimées")

    df.to_csv(FEATURES_CSV, index=False)
    print(f" features_data.csv écrit → {FEATURES_CSV.resolve()}  ({len(df):,} lignes)")
    return df

if __name__ == "__main__":
    run_features()
