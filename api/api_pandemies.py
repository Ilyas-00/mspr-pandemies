# api_pandemies.py - API FastAPI simple et clean
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import uvicorn
from api.ml_router import router as ml_router

# =========================
# Config API
# =========================
app = FastAPI(
    title="API Pandémies",
    description="API pour visualiser et prédire (taux de transmission) via IA",
    version="2.0.0",
)
# CORS (OK pour dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Connexion DB
# =========================
def get_db_connection():
    """Connexion à la base PostgreSQL"""
    try:
        # conn = psycopg2.connect(
        #     dbname="pandemies_db",
        #     user="postgres",
        #     password="Admin",    
        #     host="localhost",
        #     port="5432",
        #     cursor_factory=psycopg2.extras.RealDictCursor
        # )
        conn = psycopg2.connect(
            dbname=os.getenv("PGDATABASE", "pandemies_db"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", "Admin"),
            host=os.getenv("PGHOST", "localhost"),  # en conteneur => "db"
            port=os.getenv("PGPORT", "5432"),
            cursor_factory=psycopg2.extras.RealDictCursor
        )

        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur base de données: {e}")

# =========================
# Endpoints
# =========================


@app.get("/")
def root():
    return {
        "message": "API Pandémies",
        "endpoints": {
            "statistiques": "/stats",
            "pays": "/pays/{maladie}",
            "evolution": "/evolution/{maladie}/{pays}",
            "top_pays": "/top/{maladie}",
            "donnees_recentes": "/recent/{maladie}",
            "continents": "/continents/{maladie}",
        }
    }

@app.get("/stats")
def get_statistiques_generales():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                m.nom_maladie,
                COUNT(*)                    AS nb_records,
                COUNT(DISTINCT s.id_pays)   AS nb_pays,
                MIN(s.date_stat)            AS premiere_date,
                MAX(s.date_stat)            AS derniere_date
            FROM statistique s 
            JOIN maladie m ON s.id_maladie = m.id_maladie 
            GROUP BY m.nom_maladie
        """)
        rows = cur.fetchall()
        return {"statistiques": [dict(r) for r in rows]}
    finally:
        conn.close()

@app.get("/pays/{maladie}")
def get_pays_par_maladie(maladie: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT p.nom_pays, p.continent, p.population 
            FROM pays p
            JOIN statistique s ON p.id_pays = s.id_pays
            JOIN maladie m     ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s
            ORDER BY p.nom_pays
        """, (maladie,))
        rows = cur.fetchall()
        return {"pays": [dict(r) for r in rows]}
    finally:
        conn.close()

@app.get("/evolution/{maladie}/{pays}")
def get_evolution_pays(maladie: str, pays: str, limit: int = 100):
    """Fix: plus de comparaison à 'NaN' + COALESCE pour NULLs"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                s.date_stat,
                COALESCE(s.cas_totaux, 0)::bigint        AS cas_totaux,
                COALESCE(s.nouveaux_cas, 0)::bigint      AS nouveaux_cas,
                COALESCE(s.deces_totaux, 0)::bigint      AS deces_totaux,
                COALESCE(s.nouveaux_deces, 0)::bigint    AS nouveaux_deces
            FROM statistique s
            JOIN pays p    ON s.id_pays    = p.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s AND p.nom_pays = %s
            ORDER BY s.date_stat DESC
            LIMIT %s
        """, (maladie, pays, limit))
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail=f"Aucune donnée pour {maladie} - {pays}")
        return {"maladie": maladie, "pays": pays, "donnees": [dict(r) for r in rows]}
    finally:
        conn.close()

@app.get("/top/{maladie}")
def get_top_pays(maladie: str, limit: int = 10):
    """Fix: COALESCE au lieu des CASE + cast"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                p.nom_pays,
                p.continent,
                MAX(COALESCE(s.cas_totaux, 0))   AS max_cas,
                MAX(COALESCE(s.deces_totaux, 0)) AS max_deces
            FROM statistique s
            JOIN pays p    ON s.id_pays    = p.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s
            GROUP BY p.nom_pays, p.continent
            ORDER BY max_cas DESC
            LIMIT %s
        """, (maladie, limit))
        rows = cur.fetchall()
        return {"maladie": maladie, "top_pays": [dict(r) for r in rows]}
    finally:
        conn.close()

@app.get("/recent/{maladie}")
def get_donnees_recentes(maladie: str, jours: int = 30):
    """Fix: make_interval(days => %s) pour paramètre interval"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                s.date_stat,
                p.nom_pays,
                p.continent,
                s.cas_totaux,
                s.nouveaux_cas,
                s.deces_totaux
            FROM statistique s
            JOIN pays p    ON s.id_pays    = p.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s 
              AND s.date_stat >= (
                  SELECT MAX(date_stat) - make_interval(days => %s)
                  FROM statistique s2 
                  JOIN maladie m2 ON s2.id_maladie = m2.id_maladie 
                  WHERE m2.nom_maladie = %s
              )
            ORDER BY s.date_stat DESC, s.cas_totaux DESC
            LIMIT 100
        """, (maladie, jours, maladie))
        rows = cur.fetchall()
        return {"maladie": maladie, "periode": f"Derniers {jours} jours", "donnees": [dict(r) for r in rows]}
    finally:
        conn.close()

@app.get("/continents/{maladie}")
def get_stats_par_continent(maladie: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                p.continent,
                COUNT(DISTINCT p.nom_pays) as nb_pays,
                SUM(p.population)          as population_totale,
                MAX(COALESCE(s.cas_totaux,0)) as max_cas_pays,
                SUM(
                    CASE WHEN s.date_stat = (
                        SELECT MAX(s2.date_stat) 
                        FROM statistique s2 
                        WHERE s2.id_pays = s.id_pays 
                          AND s2.id_maladie = s.id_maladie
                    ) THEN COALESCE(s.cas_totaux,0) ELSE 0 END
                ) as cas_totaux_continent
            FROM statistique s
            JOIN pays p    ON s.id_pays    = p.id_pays
            JOIN maladie m ON s.id_maladie = m.id_maladie
            WHERE m.nom_maladie = %s 
              AND p.continent IS NOT NULL
            GROUP BY p.continent
            ORDER BY cas_totaux_continent DESC
        """, (maladie,))
        rows = cur.fetchall()
        return {"maladie": maladie, "continents": [dict(r) for r in rows]}
    finally:
        conn.close()



app.include_router(ml_router)

@app.get("/")
def root():
    return {
        "message": "API Pandémies — v2",
        "ml": {
            "health": "/ml/health",
            "predict": "/ml/predict",
            "predict_series": "/ml/predict_series/{nom_pays}",
        },
        "docs": "/docs",
    }


# =========================
# Lancement
# =========================
if __name__ == "__main__":
    print("🚀 Démarrage API Pandémies...")
    print("📊 Endpoints: http://localhost:8000/docs")
    uvicorn.run("api_pandemies:app", host="0.0.0.0", port=8000, reload=True)
