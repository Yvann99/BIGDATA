# Finistech - Data-Driven Prop Trading Platform & Alpha Detection Engine

Finistech est une plateforme de Prop Trading et un moteur d'évaluation quantitative asynchrone développés en Python. Le projet intègre un simulateur d'appariement d'ordres (Matching Engine) haute performance connecté au flux de données du CME Group (via Yahoo Finance), un module de Risk Management Big Data calculant l'Alpha Score et le Max Drawdown en temps réel, ainsi qu'une interface utilisateur multi-profils développée avec Streamlit.

---

## 💡 Genèse et Pivot Business (Démarche Itérative)

### Finistech V1 : L'infrastructure de marché low-margin (Idée Initiale)
L'intention première était de concevoir un carnet d'ordres alternatif (MTF) où la plateforme agissait comme l'unique Teneur de Marché (Market Maker) initial. Pour capter le flux d'ordres, la stratégie reposait sur une tarification agressive (spreads ultra-serrés). Les traders les plus performants devaient ensuite être promus Teneurs de Marché.

### Le Reality Check (Limites de la V1)
Le modèle V1 présentait des failles financières et structurelles majeures éliminées lors du pivot :
1. **La Sélection Adverse (Toxic Flow) :** Afficher des spreads trop serrés face à des algorithmes de Trading Haute Fréquence (HFT) mieux informés condamnait la plateforme à accumuler du stock à perte.
2. **Le Contresens de l'Alpha :** Un trader directionnel performant cherche à maximiser son *Edge* de manière confidentielle. Forcer ce profil à endosser le rôle de Market Maker (gérer des inventaires et afficher ses prix) est un non-sens métier.
3. **Barrières Réglementaires :** Le statut de place de marché multilatérale exige des fonds propres réglementaires et des licences juridiques (MiFID II) hors de portée.

### Finistech V2 : Le Pivot Prop Trading Décentralisé (Modèle Actuel)
Plutôt que de subir le risque de liquidité, Finistech exploite la force brute de son architecture de données pour devenir un **Hub de détection d'Alpha**. Le simulateur sert d'environnement d'évaluation (Challenge). Grâce au Big Data, la plateforme filtre et identifie les traders dotés d'un réel avantage statistique (flux non toxique), élimine le biais de la chance, et leur alloue un capital théorique dont la performance pourra être répliquée sur les marchés réels.

---

## 🏗️ Architecture Technique & Organisation des Fichiers

L'application est découpée selon une séparation stricte des responsabilités (approche événementielle et découplage des données) :

```bash
├── MarketTypes.py        # Enums et structures de données financières (Order, Trade, Quote, TraderProfile)
├── MatchingEngine.py     # Cœur algorithmique de la bourse : carnet d'ordres et calcul des commissions
├── Governance.py         # Module de Risk Management : calcul de l'Alpha Score et barrières de Max Drawdown
├── main.py               # Orchestrator asynchrone principal & ingestion des flux Yahoo Finance
└── Dashboard.py          # Interface graphique multi-profils interactive (Streamlit)