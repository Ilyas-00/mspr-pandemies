# etl_main.py - ETL Principal

from db_config import get_connexion
from data_cleaner import nettoyer_covid_daily, nettoyer_monkeypox, nettoyer_covid_summary

def inserer_pays(df_list):
    """Insère tous les pays uniques"""
    print("🌍 Insertion des pays...")
    
    conn = get_connexion()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Collecter tous les pays
    pays_uniques = set()
    for df in df_list:
        if 'nom_pays' in df.columns:
            pays_uniques.update(df['nom_pays'].dropna().unique())
    
    print(f"📊 {len(pays_uniques)} pays à insérer")
    
    # Insérer les pays
    for pays in sorted(pays_uniques):
        try:
            cursor.execute("""
                INSERT INTO pays (nom_pays) 
                VALUES (%s) 
                ON CONFLICT (nom_pays) DO NOTHING
            """, (pays,))
        except Exception as e:
            print(f"⚠️ Erreur pays {pays}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Pays insérés")
    return True

def inserer_statistiques_covid(df_covid):
    """Insère les statistiques COVID"""
    print("🦠 Insertion COVID...")
    
    conn = get_connexion()
    if not conn:
        return False
    
    cursor = conn.cursor()
    compteur = 0
    erreurs = 0
    
    for _, ligne in df_covid.iterrows():
        try:
            # Récupérer ID pays
            cursor.execute("SELECT id_pays FROM pays WHERE nom_pays = %s", (ligne['nom_pays'],))
            result = cursor.fetchone()
            if not result:
                continue
            id_pays = result[0]
            
            # Insérer statistique
            cursor.execute("""
                INSERT INTO statistique (
                    date_stat, id_pays, id_maladie, cas_totaux, nouveaux_cas, 
                    cas_actifs, deces_totaux, nouveaux_deces
                ) VALUES (%s, %s, 1, %s, %s, %s, %s, %s)
                ON CONFLICT (date_stat, id_pays, id_maladie) DO NOTHING
            """, (
                ligne['date_stat'], id_pays, ligne['cas_totaux'], 
                ligne['nouveaux_cas'], ligne['cas_actifs'], 
                ligne['deces_totaux'], ligne['nouveaux_deces']
            ))
            compteur += 1
            
            if compteur % 1000 == 0:
                conn.commit()  # Commit régulier
                print(f"📈 {compteur} lignes COVID insérées...")
                
        except Exception as e:
            erreurs += 1
            conn.rollback()  # Annuler la transaction en erreur
            if erreurs < 10:  # Afficher seulement les 10 premières erreurs
                print(f"⚠️ Erreur ligne COVID: {e}")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {compteur} statistiques COVID insérées, {erreurs} erreurs")
    return True

def inserer_statistiques_monkeypox(df_monkey):
    """Insère les statistiques Monkeypox"""
    print("🐒 Insertion Monkeypox...")
    
    conn = get_connexion()
    if not conn:
        return False
    
    cursor = conn.cursor()
    compteur = 0
    
    for _, ligne in df_monkey.iterrows():
        try:
            # Récupérer ID pays
            cursor.execute("SELECT id_pays FROM pays WHERE nom_pays = %s", (ligne['nom_pays'],))
            result = cursor.fetchone()
            if not result:
                continue
            id_pays = result[0]
            
            # Insérer statistique
            cursor.execute("""
                INSERT INTO statistique (
                    date_stat, id_pays, id_maladie, cas_totaux, nouveaux_cas, 
                    deces_totaux, nouveaux_deces, nouveaux_cas_lisses, 
                    nouveaux_cas_lisses_par_million
                ) VALUES (%s, %s, 2, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date_stat, id_pays, id_maladie) DO NOTHING
            """, (
                ligne['date_stat'], id_pays, ligne['cas_totaux'], 
                ligne['nouveaux_cas'], ligne['deces_totaux'], 
                ligne['nouveaux_deces'], ligne['nouveaux_cas_lisses'],
                ligne['nouveaux_cas_lisses_par_million']
            ))
            compteur += 1
            
            if compteur % 1000 == 0:
                print(f"📈 {compteur} lignes Monkeypox insérées...")
                
        except Exception as e:
            print(f"⚠️ Erreur ligne Monkeypox: {e}")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {compteur} statistiques Monkeypox insérées")
    return True

def enrichir_pays_summary(df_summary):
    """Enrichit les pays avec continent et population"""
    print("🌍 Enrichissement pays...")
    
    conn = get_connexion()
    if not conn:
        return False
    
    cursor = conn.cursor()
    compteur = 0
    
    for _, ligne in df_summary.iterrows():
        try:
            cursor.execute("""
                UPDATE pays 
                SET continent = %s, population = %s 
                WHERE nom_pays = %s
            """, (
                ligne['continent'], ligne['population'], ligne['nom_pays']
            ))
            if cursor.rowcount > 0:
                compteur += 1
        except Exception as e:
            print(f"⚠️ Erreur enrichissement {ligne['nom_pays']}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {compteur} pays enrichis")
    return True

def etl_complet():
    """Lance l'ETL complet"""
    print("🚀 DEBUT ETL PANDEMIES")
    print("=" * 40)
    
    # 1. Nettoyer les données
    try:
        covid_daily = nettoyer_covid_daily()
        monkeypox = nettoyer_monkeypox()
        covid_summary = nettoyer_covid_summary()
    except Exception as e:
        print(f"❌ Erreur nettoyage: {e}")
        return False
    
    # 2. Insérer les pays
    if not inserer_pays([covid_daily, monkeypox, covid_summary]):
        print("❌ Erreur insertion pays")
        return False
    
    # 3. Enrichir les pays
    if not enrichir_pays_summary(covid_summary):
        print("❌ Erreur enrichissement pays")
        return False
    
    # 4. Insérer les statistiques
    if not inserer_statistiques_covid(covid_daily):
        print("❌ Erreur insertion COVID")
        return False
    
    if not inserer_statistiques_monkeypox(monkeypox):
        print("❌ Erreur insertion Monkeypox")
        return False
    
    print("=" * 40)
    print("🎉 ETL TERMINE AVEC SUCCES !")
    
    # Statistiques finales
    conn = get_connexion()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pays")
        nb_pays = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM statistique")
        nb_stats = cursor.fetchone()[0]
        
        print(f"📊 Résultats finaux:")
        print(f"   Pays: {nb_pays}")
        print(f"   Statistiques: {nb_stats}")
        
        conn.close()
    
    return True

if __name__ == "__main__":
    etl_complet()