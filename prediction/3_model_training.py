# ---------------------------------------------
# 📁 prediction/3_model_training.py
# 👉 Objectif : entraîner un modèle de Machine Learning
# pour prédire le taux de transmission
# ---------------------------------------------

# ---------------------------------------------
# 1️⃣ Importer les bibliothèques
# ---------------------------------------------
import pandas as pd
# ✅ pandas : lecture et manipulation de tableaux de données

from sklearn.model_selection import train_test_split
# ✅ train_test_split : pour diviser le dataset en train et test

from sklearn.linear_model import LinearRegression
# ✅ LinearRegression : modèle simple et interprétable

from sklearn.metrics import r2_score, mean_squared_error
# ✅ Pour évaluer la qualité du modèle

import numpy as np
# ✅ Calcul numérique (racine carrée)

import joblib
# ✅ Pour sauvegarder le modèle entraîné

# ---------------------------------------------
# 2️⃣ Charger les données features
# 👉 issues de 2_features_engineering.py
# ---------------------------------------------
df = pd.read_csv("features_data.csv")
print("✅ Données chargées pour entraînement :")
print(df.head())

# ---------------------------------------------
# 3️⃣ Définir la cible et les variables explicatives
# ---------------------------------------------
# 🎯 y = ce qu'on veut prédire : le taux de transmission
y = df['taux_transmission']

# 🎯 X = variables qui expliquent y
X = df.drop(columns=['date', 'nom_pays', 'taux_transmission'])
print("\n✅ Variables explicatives :")
print(X.columns)

# ---------------------------------------------
# 4️⃣ Diviser en train et test
# ---------------------------------------------
# 👉 Pour évaluer si le modèle généralise bien
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"\n✅ Train set : {X_train.shape}")
print(f"✅ Test set : {X_test.shape}")

# ---------------------------------------------
# 5️⃣ Créer et entraîner le modèle
# ---------------------------------------------
# ✅ Choix : LinearRegression
# - Simple et interprétable
# - Suffisant pour cette preuve de concept
model = LinearRegression()
model.fit(X_train, y_train)
print("\n✅ Modèle entraîné.")

# ---------------------------------------------
# 6️⃣ Faire des prédictions sur le test
# ---------------------------------------------
y_pred = model.predict(X_test)

# ---------------------------------------------
# 7️⃣ Évaluer la qualité du modèle
# ---------------------------------------------
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("\n✅ Évaluation du modèle :")
print(f"R² (proportion de variance expliquée) : {r2:.3f}")
print(f"RMSE (Root Mean Squared Error) : {rmse:.6f}")

# ---------------------------------------------
# ✅ Explication des métriques
# - R² ≈ 1 : le modèle explique bien la variance
# - RMSE : erreur moyenne en unités de taux de transmission
# ---------------------------------------------

# ---------------------------------------------
# 8️⃣ Sauvegarder le modèle entraîné
# ---------------------------------------------
joblib.dump(model, "model_taux_transmission.pkl")
print("\n✅ Modèle sauvegardé sous model_taux_transmission.pkl ✅")