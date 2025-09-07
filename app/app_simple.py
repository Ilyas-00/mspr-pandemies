# app_simple.py - Streamlit avec login simple & rôles
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from pathlib import Path
import json

# =========================
# Config Streamlit & API
# =========================
# st.set_page_config(page_title="Dashboard Pandémies", page_icon="🦠", layout="wide")
# API_BASE_URL = "http://localhost:8000"
# =========================
# Config Streamlit & API
# =========================
import os
st.set_page_config(page_title="Dashboard Pandémies", page_icon="🦠", layout="wide")

# 1) En conteneur: on passe API_BASE_URL="http://api:8000" via docker-compose
# 2) En local (hors Docker): fallback "http://localhost:8000"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
# --- Pays & flags: lus depuis l'URL par la gateway (8511=US, 8512=FR, 8513=CH)
params = st.experimental_get_query_params()
COUNTRY = (params.get("country", ["US"])[0]).upper()
ENABLE_TECH_API = COUNTRY == "US"
ENABLE_DATAVIZ  = COUNTRY != "CH"

st.caption(f"🌍 Country: {COUNTRY} • Dataviz: {'ON' if ENABLE_DATAVIZ else 'OFF'} • ML: {'ON' if ENABLE_TECH_API else 'OFF'}")


USERS_PATH = Path("users.json")  # persistance très simple (démo)

# =========================
# Session (état) par défaut
# =========================
if "role" not in st.session_state:
    st.session_state.role = "GUEST"       # GUEST | RESEARCHER | ADMIN
if "username" not in st.session_state:
    st.session_state.username = None

# =========================
# Utilitaires users (très courts)
# =========================
def load_users() -> dict:
    """
    Charge les utilisateurs depuis users.json
    S'il n'existe pas, on crée 2 comptes de base : Admin/Admin1, Chercheur/Chercheur1
    Structure: {"Admin": {"password":"Admin1","role":"ADMIN"}, "Chercheur": {"password":"Chercheur1","role":"RESEARCHER"}}
    """
    if USERS_PATH.exists():
        try:
            return json.loads(USERS_PATH.read_text(encoding="utf-8"))
        except:
            pass
    users = {
        "Admin": {"password": "Admin1", "role": "ADMIN"},
        "Chercheur": {"password": "Chercheur1", "role": "RESEARCHER"},
    }
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")
    return users

def save_users(users: dict) -> None:
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")

USERS = load_users()

# =========================
# Fonctions API (GET) — inchangé
# =========================
@st.cache_data(ttl=300)
def get_api_data(endpoint: str):
    try:
        r = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"❌ Erreur API: {endpoint} (code {r.status_code})")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ API non disponible. Lancez : uvicorn api.api_pandemies:app --reload")
        return None
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return None

def test_api() -> bool:
    try:
        r = requests.get(f"{API_BASE_URL}/", timeout=5)
        return r.status_code == 200
    except:
        return False

# =========================
# Pages (rangées en petites fonctions)
# =========================
def page_vue_par_pays(maladie: str):
    st.header(f"📈 Données {maladie.replace('_', '-').upper()}")
    pays_data = get_api_data(f"/pays/{maladie}")
    if not (pays_data and "pays" in pays_data):
        st.error("❌ Impossible de récupérer les pays")
        return
    pays_list = [p["nom_pays"] for p in pays_data["pays"]]
    pays_choisi = st.selectbox("🌍 Choisir un pays", pays_list)
    if not pays_choisi:
        return
    evo = get_api_data(f"/evolution/{maladie}/{pays_choisi}?limit=5000")
    if not (evo and "donnees" in evo):
        st.error(f"❌ Erreur données pour {pays_choisi}")
        return
    df = pd.DataFrame(evo["donnees"])
    if df.empty:
        st.warning(f"⚠️ Aucune donnée pour {pays_choisi}")
        return
    df["date_stat"] = pd.to_datetime(df["date_stat"])
    df = df.sort_values("date_stat")
    st.subheader(f"📈 Cas totaux - {pays_choisi}")
    fig = px.line(df, x="date_stat", y="cas_totaux", title=f"Cas totaux cumulés - {pays_choisi}")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("📊 Nouveaux cas quotidiens (30 derniers jours)")
    fig2 = px.bar(df.tail(30), x="date_stat", y="nouveaux_cas")
    st.plotly_chart(fig2, use_container_width=True)

def page_comparaison(maladie: str):
    # ✅ garde pays
    if not ENABLE_DATAVIZ:
        st.warning("❌ Dataviz désactivée pour ce pays.")
        return

    st.header(f"⚖️ Comparaison {maladie.replace('_', '-').upper()}")
    pays_data = get_api_data(f"/pays/{maladie}")
    if not (pays_data and "pays" in pays_data):
        st.error("❌ Impossible de récupérer les pays")
        return
    pays_list = [p["nom_pays"] for p in pays_data["pays"]]
    col1, col2 = st.columns(2)
    with col1:
        pays1 = st.selectbox("🌍 Premier pays", pays_list, key="p1")
    with col2:
        idx2 = 1 if len(pays_list) > 1 else 0
        pays2 = st.selectbox("🌍 Deuxième pays", pays_list, index=idx2, key="p2")
    if not (pays1 and pays2 and pays1 != pays2):
        st.info("👆 Sélectionnez deux pays différents")
        return
    evo1 = get_api_data(f"/evolution/{maladie}/{pays1}?limit=5000")
    evo2 = get_api_data(f"/evolution/{maladie}/{pays2}?limit=5000")
    if not (evo1 and evo2 and "donnees" in evo1 and "donnees" in evo2):
        st.error("❌ Erreur récupération données")
        return
    df1 = pd.DataFrame(evo1["donnees"]); df1["date_stat"] = pd.to_datetime(df1["date_stat"]); df1["pays"] = pays1
    df2 = pd.DataFrame(evo2["donnees"]); df2["date_stat"] = pd.to_datetime(df2["date_stat"]); df2["pays"] = pays2
    dfc = pd.concat([df1, df2])
    if dfc.empty:
        return
    typ = st.selectbox("📈 Type de données", ["cas_totaux", "nouveaux_cas", "deces_totaux", "nouveaux_deces"])
    figc = px.line(dfc, x="date_stat", y=typ, color="pays")
    st.plotly_chart(figc, use_container_width=True)

# def page_comparaison(maladie: str):
#     st.header(f"⚖️ Comparaison {maladie.replace('_', '-').upper()}")
#     pays_data = get_api_data(f"/pays/{maladie}")
#     if not (pays_data and "pays" in pays_data):
#         st.error("❌ Impossible de récupérer les pays")
#         return
#     pays_list = [p["nom_pays"] for p in pays_data["pays"]]
#     col1, col2 = st.columns(2)
#     with col1:
#         pays1 = st.selectbox("🌍 Premier pays", pays_list, key="p1")
#     with col2:
#         idx2 = 1 if len(pays_list) > 1 else 0
#         pays2 = st.selectbox("🌍 Deuxième pays", pays_list, index=idx2, key="p2")
#     if not (pays1 and pays2 and pays1 != pays2):
#         st.info("👆 Sélectionnez deux pays différents")
#         return
#     evo1 = get_api_data(f"/evolution/{maladie}/{pays1}?limit=5000")
#     evo2 = get_api_data(f"/evolution/{maladie}/{pays2}?limit=5000")
#     if not (evo1 and evo2 and "donnees" in evo1 and "donnees" in evo2):
#         st.error("❌ Erreur récupération données")
#         return
#     df1 = pd.DataFrame(evo1["donnees"]); df1["date_stat"] = pd.to_datetime(df1["date_stat"]); df1["pays"] = pays1
#     df2 = pd.DataFrame(evo2["donnees"]); df2["date_stat"] = pd.to_datetime(df2["date_stat"]); df2["pays"] = pays2
#     dfc = pd.concat([df1, df2])
#     if dfc.empty:
#         return
#     typ = st.selectbox("📈 Type de données", ["cas_totaux", "nouveaux_cas", "deces_totaux", "nouveaux_deces"])
#     figc = px.line(dfc, x="date_stat", y=typ, color="pays")
#     st.plotly_chart(figc, use_container_width=True)

def page_taux_transmission():
    # ✅ garde pays
    if not ENABLE_TECH_API:
        st.warning("❌ API technique (ML) indisponible pour ce pays.")
        return

    st.header("📉 Taux de transmission (observé vs prédit)")
    # 1) pays disponibles côté API ML
    try:
        resp = requests.get(f"{API_BASE_URL}/ml/available_countries", timeout=10)
        resp.raise_for_status()
        countries = resp.json().get("countries", [])
    except Exception as e:
        st.error(f"Impossible de charger la liste des pays: {e}")
        return
    pays_choisi = st.selectbox("🌍 Choisir un pays", options=countries)
    if not pays_choisi:
        return
    # 2) série Observé/Prédit
    try:
        r = requests.get(f"{API_BASE_URL}/ml/predict_series/{pays_choisi}", timeout=15)
        r.raise_for_status()
        payload = r.json()
    except Exception as e:
        st.error(f"Erreur API ML: {e}")
        return
    pts = payload.get("points", [])
    if not pts:
        st.warning(f"Aucune donnée renvoyée pour {pays_choisi}")
        return
    df = pd.DataFrame(pts); df["date"] = pd.to_datetime(df["date"])
    plot_df = df.melt(id_vars=["date"], value_vars=["taux_true","taux_pred"], var_name="type", value_name="taux")
    plot_df["type"] = plot_df["type"].map({"taux_true": "Observé", "taux_pred": "Prédit"})
    fig = px.line(plot_df, x="date", y="taux", color="type", labels={"date":"Date","taux":"Taux de transmission"})
    st.plotly_chart(fig, use_container_width=True)
    if df["taux_true"].notna().any():
        d2 = df.dropna(subset=["taux_true"])
        mae = (d2["taux_pred"] - d2["taux_true"]).abs().mean()
        rmse = (((d2["taux_pred"] - d2["taux_true"])**2).mean())**0.5
        st.caption(f"Écarts • MAE: {mae:.2e}  |  RMSE: {rmse:.2e}")
    else:
        st.caption("Écarts non calculés (taux_true absent).")

# def page_taux_transmission():
#     st.header("📉 Taux de transmission (observé vs prédit)")
#     # 1) pays disponibles côté API ML
#     try:
#         resp = requests.get(f"{API_BASE_URL}/ml/available_countries", timeout=10)
#         resp.raise_for_status()
#         countries = resp.json().get("countries", [])
#     except Exception as e:
#         st.error(f"Impossible de charger la liste des pays: {e}")
#         return
#     pays_choisi = st.selectbox("🌍 Choisir un pays", options=countries)
#     if not pays_choisi:
#         return
#     # 2) série Observé/Prédit
#     try:
#         r = requests.get(f"{API_BASE_URL}/ml/predict_series/{pays_choisi}", timeout=15)
#         r.raise_for_status()
#         payload = r.json()
#     except Exception as e:
#         st.error(f"Erreur API ML: {e}")
#         return
#     pts = payload.get("points", [])
#     if not pts:
#         st.warning(f"Aucune donnée renvoyée pour {pays_choisi}")
#         return
#     df = pd.DataFrame(pts); df["date"] = pd.to_datetime(df["date"])
#     plot_df = df.melt(id_vars=["date"], value_vars=["taux_true","taux_pred"], var_name="type", value_name="taux")
#     plot_df["type"] = plot_df["type"].map({"taux_true": "Observé", "taux_pred": "Prédit"})
#     fig = px.line(plot_df, x="date", y="taux", color="type", labels={"date":"Date","taux":"Taux de transmission"})
#     st.plotly_chart(fig, use_container_width=True)
#     if df["taux_true"].notna().any():
#         d2 = df.dropna(subset=["taux_true"])
#         mae = (d2["taux_pred"] - d2["taux_true"]).abs().mean()
#         rmse = (((d2["taux_pred"] - d2["taux_true"])**2).mean())**0.5
#         st.caption(f"Écarts • MAE: {mae:.2e}  |  RMSE: {rmse:.2e}")
#     else:
#         st.caption("Écarts non calculés (taux_true absent).")

def page_admin_accounts():
    st.header("👥 Comptes chercheurs (Admin)")

    # --- Tableau des utilisateurs (lecture) ---
    df_users = pd.DataFrame(
        [{"username": u, "role": USERS[u]["role"]} for u in USERS]
    ).sort_values("role")
    st.subheader("Liste des utilisateurs")
    st.table(df_users)

    # --- Création d'un compte Chercheur (formulaire simple) ---
    st.subheader("Créer un compte Chercheur")
    with st.form("create_user"):
        new_user = st.text_input("Identifiant")
        new_pwd = st.text_input("Mot de passe", type="password")
        create_ok = st.form_submit_button("Créer")
    if create_ok:
        if not new_user or not new_pwd:
            st.warning("Renseigne un identifiant et un mot de passe.")
        elif new_user in USERS:
            st.error("Cet identifiant existe déjà.")
        else:
            USERS[new_user] = {"password": new_pwd, "role": "RESEARCHER"}
            save_users(USERS)
            st.success(f"Compte créé: {new_user} (RESEARCHER)")
            st.rerun()

    # --- Suppression de comptes Chercheur (multi-sélection) ---
    st.subheader("Supprimer des comptes Chercheur")
    # On ne propose pas 'Admin' à la suppression
    researcher_accounts = [u for u, v in USERS.items() if v.get("role") == "RESEARCHER"]
    to_delete = st.multiselect("Sélectionne les comptes à supprimer", researcher_accounts)

    # Confirmation via formulaire pour éviter les clics accidentels
    with st.form("delete_users"):
        confirm = st.checkbox("Je confirme la suppression des comptes sélectionnés.")
        delete_ok = st.form_submit_button("Supprimer")
    if delete_ok:
        if not to_delete:
            st.info("Aucun compte sélectionné.")
        elif not confirm:
            st.warning("Merci de cocher la confirmation avant de supprimer.")
        else:
            for u in to_delete:
                USERS.pop(u, None)
            save_users(USERS)
            st.success(f"Comptes supprimés : {', '.join(to_delete)}")
            st.rerun()


# =========================
# Auth & Navigation
# =========================
def sidebar_auth_and_nav():
    role = st.session_state.role

    # Pages de base
    pages = ["📈 Vue par pays"]  # toujours visible

    # Dataviz seulement si autorisée ET rôle suffisant
    if ENABLE_DATAVIZ and role in ("RESEARCHER", "ADMIN"):
        pages += ["⚖️ Comparaison pays"]

    # API technique (ML) seulement aux pays autorisés (US) ET rôle suffisant
    if ENABLE_TECH_API and role in ("RESEARCHER", "ADMIN"):
        pages += ["📉 Taux de transmission"]

    # Admin
    if role == "ADMIN":
        pages += ["👥 Comptes chercheurs"]

    # Connexion/Déconnexion
    st.sidebar.markdown("---")
    st.sidebar.write(
        f"Rôle actuel : **{role}**"
        + (f" (👤 {st.session_state.username})" if st.session_state.username else "")
    )
    if role == "GUEST":
        if st.sidebar.button("🔐 Connexion"):
            st.session_state.show_login = True
    else:
        if st.sidebar.button("🚪 Déconnexion"):
            st.session_state.role = "GUEST"
            st.session_state.username = None
            st.session_state.show_login = False

    page = st.sidebar.selectbox("📊 Choisir une page", pages, index=0)

    maladie = st.sidebar.selectbox(
        "🦠 Maladie",
        ["covid_19", "monkeypox"],
        index=0,
        format_func=lambda x: {"covid_19":"🦠 COVID-19 (2020-2022)",
                               "monkeypox":"🐒 Monkeypox (2022-2023)"}[x]
    )
    return page, maladie

# def sidebar_auth_and_nav():
#     # ——— Filtre pages selon le rôle ———
#     role = st.session_state.role
#     pages = ["📈 Vue par pays"]  # visible pour tout le monde (y compris GUEST)
#     if role in ("RESEARCHER", "ADMIN"):
#         pages += ["⚖️ Comparaison pays", "📉 Taux de transmission"]
#     if role == "ADMIN":
#         pages += ["👥 Comptes chercheurs"]

#     # ——— Connexion/Déconnexion ———
#     st.sidebar.markdown("---")
#     st.sidebar.write(f"Rôle actuel : **{role}**" + (f" (👤 {st.session_state.username})" if st.session_state.username else ""))
#     if role == "GUEST":
#         if st.sidebar.button("🔐 Connexion"):
#             st.session_state.show_login = True
#     else:
#         if st.sidebar.button("🚪 Déconnexion"):
#             st.session_state.role = "GUEST"
#             st.session_state.username = None
#             st.session_state.show_login = False

#     # ——— Choix page uniquement quand pas sur écran login ———
#     page = st.sidebar.selectbox("📊 Choisir une page", pages, index=0)
#     # ——— Sélecteur commun (maladie) ———
#     maladie = st.sidebar.selectbox(
#         "🦠 Maladie",
#         ["covid_19", "monkeypox"],
#         index=0,
#         format_func=lambda x: {"covid_19": "🦠 COVID-19 (2020-2022)", "monkeypox": "🐒 Monkeypox (2022-2023)"}[x]
#     )
#     return page, maladie

def login_screen():
    st.header("🔐 Connexion")
    with st.form("login"):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        ok = st.form_submit_button("Se connecter")
    if ok:
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.session_state.show_login = False
            st.success(f"Bienvenue {username} — rôle: {user['role']}")
            st.rerun()
        else:
            st.error("Identifiants invalides")

# =========================
# App
# =========================
def main():
    st.title("🦠 Dashboard Pandémies")

    # Ping API (comme avant)
    if not test_api():
        st.error("🚨 API non disponible !")
        st.stop()
    st.success("✅ API connectée")

    # Affiche l'écran de login si demandé
    if "show_login" not in st.session_state:
        st.session_state.show_login = False
    if st.session_state.show_login:
        login_screen()
        return

    # Barre latérale (pages + maladie + auth)
    page, maladie = sidebar_auth_and_nav()

    # Routage minimal selon la page
    if page == "📈 Vue par pays":
        page_vue_par_pays(maladie)
    elif page == "⚖️ Comparaison pays":
        page_comparaison(maladie)
    elif page == "📉 Taux de transmission":
        page_taux_transmission()
    elif page == "👥 Comptes chercheurs":
        if st.session_state.role == "ADMIN":
            page_admin_accounts()
        else:
            st.error("Accès refusé.")

if __name__ == "__main__":
    main()
