# Commodity Market Maker - Big Data Trading System

## Présentation du Projet
Ce projet modélise l'aspect business et technique de la gestion de données massives dans un contexte de finance de marché. L'objectif est de construire un **Trading Book** sur matières premières (Commodities) où nous agissons en tant que **Market Maker**. 

Le système se porte contrepartie de chaque transaction, capture une marge (spread) et ajuste celle-ci dynamiquement en analysant le comportement des traders (détection du flux informé ou "Toxic Flow") afin de gérer la couverture et la rentabilité.

## Architecture du Système (Pipeline Asynchrone)

Le projet repose sur une architecture non-bloquante utilisant `asyncio` pour gérer la haute densité d'événements :

1. **Génération de Flux (Monkey Trader) :** Simulation de haute intensité générant des milliers d'ordres simultanés (ex: 10 000 ordres en 5 secondes) pour éprouver la robustesse du système.
2. **Ingestion & Queue :** Utilisation de `asyncio.Queue` pour centraliser les flux, gérer l'asynchronisme et garantir l'intégrité des données en évitant les *Data Races*.
3. **Moteur de Traitement (Engine) :** Consommation des ordres, validation des transactions et mise à jour en temps réel du Trading Book.
4. **Algo de Spread Dynamique :** Intelligence métier analysant l'Alpha des traders, l'élasticité au prix et les corrélations inter-produits pour ajuster les marges.
5. **Interface Client (Streamlit) :** Dashboard interactif permettant le passage d'ordres manuels, la visualisation des positions et le suivi live des prix via API.

## 🛠️ Stack Technique
* **Langage :** Python 3.10+
* **Concurrence :** `asyncio` (Programmation asynchrone)
* **Stockage Big Data :** Format **Parquet** (PyArrow) pour la performance en lecture/écriture.
* **Visualisation :** Streamlit.
* **Données Marché :** Intégration API (yFinance / CCXT).

## 📂 Structure du Projet
```text
├── app/                # Frontend Streamlit
├── engine/             # Cœur du système (Matching & Trading Book)
├── analytics/          # Stratégies de Spread & Analyse comportementale
├── ingestion/          # Monkey Traders & Gestion de la file d'attente
├── data/               # Stockage persistant (Fichiers Parquet)
└── main.py             # Orchestrateur du système asynchrone