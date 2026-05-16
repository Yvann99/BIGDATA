# LiquidityHub - Simulateur de Marché Asynchrone et Tableau de Bord Multi-Profils

LiquidityHub est une plateforme de simulation de marché financier (matching engine) développée en Python. Elle combine un moteur d'exécution d'ordres asynchrone connecté à l'API Yahoo Finance, un module de gouvernance algorithmique (Alpha Score), et une interface utilisateur interactive multi-profils développée avec Streamlit.

Ce projet met en pratique des concepts clés de la finance quantitative, du Big Data et du développement logiciel haute performance : asynchronisme (`asyncio`), stockage colonnaire optimisé (`Parquet`), flux de données temps réel (`JSON Lines`), et calculs de gestion des risques (PnL Mark-to-Market, inventaires, spreads).

---

## Architecture du Projet

Le projet est articulé autour de 5 fichiers principaux, garantissant une séparation stricte des responsabilités (Modèle-Vue-Contrôleur) :

1. **`MarketTypes.py`** : Définition des structures de données financières de base (`Order`, `Trade`, `Quote`, `Side`, `Role`, `TraderProfile`) à l'aide de types énumérés et d'objets structurés.
2. **`MatchingEngine.py`** : Cœur de la bourse. Gère le carnet d'ordres, l'exécution des ordres d'achat/vente par rapport aux cotations actives, et prélève une commission de 0,02 % sur les volumes financiers échangés.
3. **`Governance.py`** : Module d'analyse quantitative. Il calcule en temps réel l'Alpha Score de chaque trader en mesurant l'impact de ses ordres sur le marché à court terme. Si les performances d'un trader automatique dépassent un certain seuil, la gouvernance le promeut automatiquement au rang de Market Maker (LP).
4. **`main.py`** : Orchestrateur central de l'application. Il pilote la boucle asynchrone globale, simule l'activité de 15 robots de trading alternatifs, traite les demandes manuelles en provenance de l'interface, et interroge de manière non bloquante l'API Yahoo Finance avec un dispositif de sécurité (Timeout et Fallback).
5. **`Dashboard.py`** : Interface graphique multi-profils (Streamlit) permettant d'explorer et d'interagir avec le marché sous trois angles métiers différents.

---

## Fonctionnalités Clés et Concepts Mis en Œuvre

### Concurrence et Asynchronisme (`asyncio`)
Le moteur de matching et les 15 traders algorithmiques tournent simultanément de manière asynchrone. L'interrogation des cours de bourse réels internationaux (CME, ICE, CBOT via `yfinance`) s'effectue dans un thread de fond indépendant (`asyncio.to_thread`) avec un Timeout de 2 secondes maximum, évitant ainsi tout gel ou ralentissement du moteur, même le week-end lorsque les API de flux sont fermées.

### Performance Big Data (`Parquet` et `JSON`)
* **`dashboard_trades.parquet`** : L'historique complet de la bourse est sauvegardé au format Parquet (stockage colonnaire compressé). Ce format garantit des performances d'analyse quantitative optimales (Big Data) tout en isolant les structures de données pures de la bourse des données enrichies pour l'interface.
* **`pending_orders.json`** : Fichier servant de bus de messages (Message Queue léger) permettant une communication asynchrone unidirectionnelle entre l'interface Streamlit et le moteur principal.

### Gestion des Risques et Logique Métier Financière
* **Vue Trader Client** : Permet de passer des ordres d'achat/vente manuels via un ticket d'ordre et de suivre l'historique de ses propres exécutions.
* **Vue Market Maker Promu (LP)** : Permet aux fournisseurs de liquidité de piloter leurs expositions nettes (positions Long, Short ou Flat) sur 5 commodités majeures (`CL=F` Pétrole, `GC=F` Or, `NG=F` Gaz, `HG=F` Cuivre, `ZC=F` Maïs). Elle intègre un calcul dynamique du PnL Réalisé et du PnL Latent (Mark-to-Market) mis à jour selon le cours spot de l'API. Un terminal dédié permet d'injecter des Quotes personnalisées (Bid/Ask/Volume) en paramétrant un spread cible (%).
* **Vue Opérateur Business** : Tour de contrôle offrant une visibilité à 360° sur la plateforme. Elle affiche le volume global, le nombre de transactions totales, le Chiffre d'Affaires réel généré par les commissions de la plateforme (0,02 %), le flux complet des transactions ainsi qu'un Leaderboard dynamique classant les teneurs de marché actifs avec leurs prix en direct.

---

## Structure du Dépôt GitHub

```bash
├── Dashboard.py          # Interface utilisateur Streamlit (IHM multi-profils)
├── MarketTypes.py        # Énumérations et modèles de données (Order, Trade, Quote...)
├── MatchingEngine.py     # Logique de matching et gestion des carnets de spreads
├── Governance.py         # Calcul de l'Alpha Score et promotion des traders
├── main.py               # Orchestrator asynchrone principal & flux de l'API Yahoo Finance
├── data/                 # Dossier local de stockage des données (généré automatiquement)
│   ├── dashboard_trades.parquet  # Base colonnaire enrichie pour le Dashboard
│   ├── executed_trades.parquet   # Historique brut pour le module de Gouvernance
│   └── pending_orders.json       # Bus de communication IHM -> Moteur
├── .gitignore            # Fichier d'exclusion pour conserver un dépôt propre
└── README.md             # Présentation et documentation du projet (Ce fichier)