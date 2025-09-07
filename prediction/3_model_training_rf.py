# prediction/3_model_training_rf.py
import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import r2_score, mean_squared_error

from prediction.config import FEATURES_CSV, MODEL_PATH, FEATURE_COLS, TARGET_COL

RANDOM_STATE = 42

def run_train():
    print("🏋️ Entraînement du modèle Random Forest (cible = taux_transmission)")
    data = pd.read_csv(FEATURES_CSV, parse_dates=["date_stat"])

    # X / y
    X = data[FEATURE_COLS].copy()
    y = data[TARGET_COL].astype(float).values

    # Split simple (note : pour du vrai time series, préférer un split temporel)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    # Grille d'hyperparamètres
    param_grid = {
        "n_estimators": [300, 600],
        "max_depth": [None, 15, 30],
        "min_samples_split": [2, 5, 10],
        "max_features": ["sqrt", "log2", None],
    }

    rf = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=2)
    gs = GridSearchCV(
        rf,
        param_grid=param_grid,
        scoring="neg_mean_squared_error",
        cv=3,
        n_jobs=2,   
        verbose=2,
    )

    gs.fit(X_train, y_train)

    best = gs.best_estimator_
    print(f" Best params: {gs.best_params_}")

    # Évaluation
    y_pred = best.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    print(f" R² (test): {r2:.4f} | RMSE (test): {rmse:.6f}")

    # Sauvegarde
    dump(best, MODEL_PATH)
    print(f" Modèle sauvegardé → {MODEL_PATH.resolve()}")

    # Retour métriques pour log
    return {"r2": float(r2), "rmse": float(rmse), "best_params": gs.best_params_}

if __name__ == "__main__":
    run_train()
