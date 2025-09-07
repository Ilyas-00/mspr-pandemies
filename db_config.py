# db_config.py - Connexion à la base de données

# import psycopg2

# def get_connexion():
    
#     try:
#         conn = psycopg2.connect(
#             dbname='pandemies_db',
#             user='postgres',
#             password='Admin',
#             host='localhost',
#             port='5432',
#             connect_timeout=5
#         )
#         return conn
#     except Exception as e:
#         print(f" Erreur connexion: {e}")
#         return None
# db_config.py (patch minimal)
import os
import psycopg2

def get_connexion():
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE", "pandemies_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "Admin"),
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        connect_timeout=5
    )


if __name__ == "__main__":
    try:
        conn = get_connexion()
        if not conn:
            print("❌ Connexion échouée")
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                print("🎉 CONNEXION RÉUSSIE !")
                print("PostgreSQL:", cur.fetchone()[0])
            conn.close()
    except Exception as e:
        print("❌ Erreur:", e)
