# MSPR Pandémies – Data Engineering & Analytics Platform

## Description
Ce projet est une plateforme complète d’analyse de données sur les pandémies.  
Il permet de collecter, transformer et analyser des données sanitaires afin de produire des visualisations et des prédictions.

Le projet couvre l'ensemble du pipeline data : ingestion, traitement, stockage, exposition via API et visualisation dans un dashboard.

## Architecture du projet

Le projet est structuré autour de plusieurs composants :

- **ETL Pipeline** : traitement et nettoyage des fichiers CSV contenant les données
- **Base de données PostgreSQL** : stockage structuré des données après transformation
- **API** : exposition des données et des prédictions
- **Modèle d'intelligence artificielle** : modèle entraîné pour générer des prédictions
- **Dashboard** : interface permettant de visualiser les données et les résultats du modèle
- **Monitoring & Docker** : gestion des services et conteneurisation de l'application

## Pipeline de données

1. Ingestion des données depuis des fichiers CSV
2. Nettoyage et transformation des données
3. Modélisation des données (MCD / MLD)
4. Chargement dans une base de données PostgreSQL
5. Exposition des données via une API
6. Visualisation et analyse dans un dashboard
7. Génération de prédictions avec un modèle de machine learning

## Technologies utilisées

- **Python**
- **PostgreSQL**
- **Docker / Docker Compose**
- **API REST**
- **Machine Learning (modèle .pkl)**
- **Data processing (ETL)**

## Structure du projet

- api/          (API pour exposer les données et prédictions)
- app/          (logique applicative)
- data/         (fichiers de données)
- prediction/   (modèle d'intelligence artificielle)
- monitoring/   (monitoring des services)
- docker/       (configuration des conteneurs)
- tests/   (tests du projet)


## Objectif du projet

Construire une architecture complète de traitement et d'analyse de données permettant de transformer des données brutes en informations exploitables et visualisables.
