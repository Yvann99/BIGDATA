# 🏛️ LiquidityHub: Multilateral Trading Facility (MTF) & Hybrid Liquidity Marketplace

**LiquidityHub** est une plateforme de marché hybride évolutive conçue pour transformer l'activité de Market Making traditionnelle en un écosystème collaboratif, régulé et dicté par la donnée (*Data-Driven*).

---

## 🔍 Vision Stratégique & Modèle Évolutif

Le projet résout le problème de la **sélection adverse** en inversant le rapport de force entre la plateforme et les traders informés à travers un déploiement en trois phases.

### Phase 1 : L'Amorçage (La Plateforme est MM)
* **L'attraction :** La plateforme utilise ses propres algorithmes et son capital pour afficher des prix d'achat au plus haut et des prix de vente au plus bas (spreads ultra-serrés).
* **Le but :** Servir de produit d'appel pour forcer les traders du marché à venir exécuter leurs ordres chez nous, générant ainsi une masse critique de données brutes.
* **Le risque :** Accepter de subir des pertes initiales face aux traders "informés" pour découvrir leur identité et capturer leur comportement.

### Phase 2 : L'Analyse Post-Trade (Le Scouting)
* **Capture des flux :** Stockage permanent et asynchrone de toutes les exécutions au format haute performance **Parquet**.
* **Calcul de l'Alpha Score :** Mesure mathématique du décalage des cours après chaque trade. Si le prix du marché décale systématiquement dans le sens d'un client juste après son exécution, la plateforme identifie un "trader informé" possédant une information supérieure à notre propre algorithme.

### Phase 3 : La Plateforme devient Courtier (La Plateforme possède les MM)
* **La bascule automatique :** La gouvernance promeut ces traders d'élite du statut de `TRADER` à `MARKET_MAKER`.
* **Le transfert de risque :** Les traders promus déploient leur propre capital et leurs algorithmes supérieurs pour animer le marché à notre place.
* **Monétisation finale :** La plateforme se retire progressivement du risque de marché direct pour devenir un courtier pur, encaissant une commission sur chaque match entre clients et MM promus.

---

## 🛠️ Architecture du Système

### 1. Le Moteur de Matching (`MatchingEngine.py`)
Le cœur du système qui centralise tous les ordres et fait correspondre les acheteurs avec le **Meilleur Prix Anonymisé** disponible parmi les différents MM actifs (le MM Original de la plateforme ou les MM promus).

### 2. Algorithme de Gouvernance (`Governance.py`)
Pour garantir l'intégrité du marché et la gestion du cycle de vie des membres :
* **Scouting d'Alpha :** Traitement statistique des métriques post-trade pour détecter le flux toxique/informé.
* **Anti-Monopole :** Calcul de la concentration de la liquidité (Indice HHI) pour empêcher un seul MM externe de saturer le carnet d'ordres.
* **Anonymat Total :** Les identités réelles des MM sont masquées derrière des alias (`LP-XXXXXX`) pour protéger leurs stratégies du reverse-engineering.

### 3. Dashboard Temps Réel (`Dashboard.py`)
Une interface opérateur complète développée sous **Streamlit** intégrant :
* Le carnet d'ordres consolidé (Best Bid / Best Offer).
* Le leaderboard anonymisé des fournisseurs de liquidité.
* Le panneau de contrôle du volume et de passage d'ordres clients (Terminal Trader).
* Le monitoring des commissions de courtage générées en direct.

---

## ⚖️ Différence Structurelle : Trader vs Market Maker

Le passage du statut de client à celui de partenaire modifie radicalement la mécanique d'interaction avec l'infrastructure :

| Caractéristique | En tant que TRADER (Subit le marché) | En tant que MARKET_MAKER (Fait le marché) |
| :--- | :--- | :--- |
| **Type de Message** | Ordres directionnels et asymétriques (Achat OU Vente). | Message unique : La `Quote` (Double-Cote simultanée). |
| **Exécution** | Doit séquencer ses ordres dans le temps pour ouvrir/fermer une position. | Affiche ses prix d'achat (Bid) et de vente (Ask) en continu. |
| **Complexité** | Supporte la gestion du timing et le risque d'exécution. | Laisse le moteur insérer ses prix tout en haut du carnet via le badge *Verified LP*. |
| **Rémunération** | Paye le spread ou la commission pour entrer sur le marché. | Capture le *spread* de manière passive en fournissant de la liquidité. |

---

## 🚀 Stack Technique

* **Langage :** Python 3.11+ (Optimisé pour Python 3.14+)
* **Concurrence & Asynchronisme :** `asyncio` pour la gestion simultanée des flux de cotation et des carnets d'ordres.
* **Stockage de Données :** `Pandas` & `PyArrow` (Format Parquet avec mécanisme d'écriture atomique via Shadow Writing).
* **Communication Inter-Processus :** File d'attente asynchrone sur disque (`pending_orders.json`) assurant le découplage entre le serveur Web et le moteur d'exécution.
* **Interface Graphique :** `Streamlit` avec architecture moderne en `st.fragment` pour le rafraîchissement haute fréquence.