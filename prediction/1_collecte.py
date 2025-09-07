# prediction/1_collecte.py
import os
import pandas as pd
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

from prediction.config import CLEAN_DATA_CSV, MALADIE_CIBLE

load_dotenv() 

def get_conn():
    conn = psycopg2.connect(
        dbname=os.getenv("PGDATABASE", "pandemies_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "Admin"),
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    return conn

SQL = """
SELECT 
    s.date_stat,
    p.nom_pays,
    p.continent,
    p.population,
    COALESCE(s.nouveaux_cas, 0)::bigint AS nouveaux_cas,
    COALESCE(s.cas_totaux, 0)::bigint   AS cas_totaux
FROM statistique s
JOIN pays p    ON s.id_pays = p.id_pays
JOIN maladie m ON s.id_maladie = m.id_maladie
WHERE m.nom_maladie = %s
ORDER BY p.nom_pays, s.date_stat;
"""

def run_collect(maladie: str = MALADIE_CIBLE):
    print(f" Collecte depuis PostgreSQL pour: {maladie}")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL, (maladie,))
            rows = cur.fetchall()
    df = pd.DataFrame(rows)

    # Nettoyage minimal
    df["date_stat"] = pd.to_datetime(df["date_stat"])
    df = df[df["population"].fillna(0) > 0]
    df = df[df["nouveaux_cas"].fillna(0) >= 0]
    df = df[df["cas_totaux"].fillna(0) >= 0]

    df.sort_values(["nom_pays", "date_stat"], inplace=True)
    df.to_csv(CLEAN_DATA_CSV, index=False)
    print(f"clean_data.csv écrit → {CLEAN_DATA_CSV.resolve()}  ({len(df):,} lignes)")
    return df

if __name__ == "__main__":
    run_collect()
