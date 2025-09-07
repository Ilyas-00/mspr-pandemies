# data_cleaner.py - Nettoyage des données

import pandas as pd
import unicodedata

def nettoyer_nom_pays(nom):
    """Enlève accents et normalise le nom"""
    if not nom or pd.isna(nom):
        return ""
    
    # Supprimer accents
    nom = unicodedata.normalize('NFD', str(nom))
    nom = ''.join(c for c in nom if unicodedata.category(c) != 'Mn')
    
    # Minuscules et remplacer espaces/caractères spéciaux
    nom = nom.lower().strip()
    nom = nom.replace(' ', '_').replace("'", "").replace('-', '_')
    
    return nom

def nettoyer_covid_daily():
    """Nettoie le fichier COVID quotidien"""
    print("🧹 Nettoyage COVID daily...")
    
    df = pd.read_csv("data/worldometer_coronavirus_daily_data.csv")
    print(f"📊 Lignes avant: {len(df)}")
    
    # Garder colonnes utiles
    df = df[['date', 'country', 'cumulative_total_cases', 'daily_new_cases', 
             'active_cases', 'cumulative_total_deaths', 'daily_new_deaths']].copy()
    
    # Renommer
    df.columns = ['date_stat', 'nom_pays', 'cas_totaux', 'nouveaux_cas', 
                  'cas_actifs', 'deces_totaux', 'nouveaux_deces']
    
    # IMPORTANT: Supprimer continents AVANT de nettoyer les noms
    continents_originaux = ['World', 'Africa', 'Asia', 'Europe', 'North America', 
                           'South America', 'Oceania', 'Antarctica']
    df = df[~df['nom_pays'].isin(continents_originaux)]
    print(f"📊 Après suppression continents: {len(df)}")
    
    # Maintenant nettoyer les noms
    df['nom_pays'] = df['nom_pays'].apply(nettoyer_nom_pays)
    
    # Supprimer lignes vides
    df = df.dropna(subset=['date_stat', 'nom_pays'])
    df = df.drop_duplicates()
    
    print(f"📊 Lignes après: {len(df)}")
    return df

def nettoyer_monkeypox():
    """Nettoie le fichier Monkeypox"""
    print("🧹 Nettoyage Monkeypox...")
    
    df = pd.read_csv("data/owid-monkeypox-data.csv")
    print(f"📊 Lignes avant: {len(df)}")
    
    # Garder colonnes utiles
    df = df[['date', 'location', 'total_cases', 'new_cases', 'total_deaths', 
             'new_deaths', 'new_cases_smoothed', 'new_cases_smoothed_per_million']].copy()
    
    # Renommer
    df.columns = ['date_stat', 'nom_pays', 'cas_totaux', 'nouveaux_cas', 
                  'deces_totaux', 'nouveaux_deces', 'nouveaux_cas_lisses', 
                  'nouveaux_cas_lisses_par_million']
    
    # IMPORTANT: Supprimer continents AVANT de nettoyer les noms
    continents_originaux = ['World', 'Africa', 'Asia', 'Europe', 'North America', 
                           'South America', 'Oceania', 'Antarctica']
    df = df[~df['nom_pays'].isin(continents_originaux)]
    print(f"📊 Après suppression continents: {len(df)}")
    
    # Maintenant nettoyer les noms
    df['nom_pays'] = df['nom_pays'].apply(nettoyer_nom_pays)
    
    # Supprimer lignes vides
    df = df.dropna(subset=['date_stat', 'nom_pays'])
    df = df.drop_duplicates()
    
    print(f"📊 Lignes après: {len(df)}")
    return df

def nettoyer_covid_summary():
    """Nettoie le fichier COVID résumé"""
    print("🧹 Nettoyage COVID summary...")
    
    df = pd.read_csv("data/worldometer_coronavirus_summary_data.csv")
    print(f"📊 Lignes avant: {len(df)}")
    
    # Garder colonnes utiles
    df = df[['country', 'continent', 'population', 'total_recovered', 'serious_or_critical']].copy()
    
    # Renommer
    df.columns = ['nom_pays', 'continent', 'population', 'total_gueris', 'cas_graves']
    
    # Nettoyer pays
    df['nom_pays'] = df['nom_pays'].apply(nettoyer_nom_pays)
    
    # Supprimer continents
    continents = ['world', 'africa', 'asia', 'europe', 'north_america', 
                  'south_america', 'oceania']
    df = df[~df['nom_pays'].isin(continents)]
    
    # Supprimer lignes vides
    df = df.dropna(subset=['nom_pays'])
    df = df.drop_duplicates()
    
    print(f"📊 Lignes après: {len(df)}")
    return df

if __name__ == "__main__":
    print("🧹 Test nettoyage données")
    
    # Test fonction nettoyage nom
    tests = ["França", "United States", "Côte d'Ivoire"]
    for nom in tests:
        print(f"'{nom}' -> '{nettoyer_nom_pays(nom)}'")
    
    print("\n📁 Test nettoyage fichiers:")
    
    # Test COVID daily
    try:
        covid_daily = nettoyer_covid_daily()
        print(f"✅ COVID daily: {len(covid_daily)} lignes nettoyées")
    except Exception as e:
        print(f"⚠️ Erreur COVID daily: {e}")
    
    # Test Monkeypox
    try:
        monkeypox = nettoyer_monkeypox()
        print(f"✅ Monkeypox: {len(monkeypox)} lignes nettoyées")
    except Exception as e:
        print(f"⚠️ Erreur Monkeypox: {e}")
    
    # Test COVID summary
    try:
        covid_summary = nettoyer_covid_summary()
        print(f"✅ COVID summary: {len(covid_summary)} lignes nettoyées")
    except Exception as e:
        print(f"⚠️ Erreur COVID summary: {e}")