# 🏛️ LiquidityHub: Multilateral Trading Facility (MTF) & MM Management

**LiquidityHub** est une plateforme de trading haute performance conçue pour transformer l'activité de Market Making traditionnelle en un écosystème collaboratif et régulé. 

Le projet simule une place de marché où les traders les plus performants sont identifiés par la donnée, promus au rang de **Fournisseurs de Liquidité (MM)**, et dotés de capital pour animer le marché, tandis que la plateforme agit comme un courtier centralisé (Broker) prélevant des commissions de gestion.

---

## 🔍 Vision Stratégique

L'objectif est de posséder une armée de Market Makers spécialisés, offrant les prix les plus compétitifs du marché tout en restant sous l'ombrelle technologique et régulatrice de la plateforme.

1. **Phase d'Attraction :** Utilisation de spreads ultra-serrés (produit d'appel) pour capter un flux massif de données.
2. **Phase d'Identification :** Analyse de la sélection adverse pour repérer les traders "informés" (ceux qui ont une meilleure lecture du marché que l'algorithme de base).
3. **Phase de Promotion :** Transformation de ces traders en Market Makers délégués.
4. **Phase de Scalabilité :** Domination du marché par une multitude de MM anonymes agissant pour le compte du groupe.

---

## 🛠️ Architecture du Système

### 1. Le Moteur de Matching (Matching Engine)
Le cœur du système qui centralise tous les ordres et fait correspondre les acheteurs avec le **Meilleur Prix Anonymisé** disponible parmi les différents MM actifs.

### 2. Algorithme de Gouvernance
Pour garantir l'intégrité du marché, la plateforme impose des règles strictes :
* **Anti-Monopole :** Empêche un seul MM de devenir "le marché" pour limiter le risque systémique.
* **Limites d'Exposition :** Gestion dynamique du capital alloué selon la performance.
* **Anonymat Total :** Les prix sont affichés sans l'identité du MM pour éviter l'arbitrage externe et le reverse-engineering de stratégie.

### 3. Dashboard "Market Intelligence"
Une interface temps réel affichant :
* Le carnet d'ordres (Order Book) consolidé.
* Le leaderboard des MM basé sur le **Taux de Réussite** et la **Consistance**.
* Les revenus de commission générés par la plateforme.

---

## 📈 Indicateurs de Performance (KPIs)

* **Alpha Leakage :** Mesure de la perte de valeur face aux traders informés avant leur promotion.
* **Market Share par MM :** Suivi de la concentration de la liquidité.
* **Commission Yield :** Rentabilité nette de la plateforme par trade effectué.
* **Slippage Client :** Écart entre le prix demandé et le prix exécuté, garantissant la compétitivité.

---

## 🚀 Stack Technique

* **Langage :** Python 3.11+
* **Concurrence :** `asyncio` pour la gestion des flux d'ordres massifs.
* **Data Processing :** `Pandas` & `PyArrow` (Format Parquet pour le Big Data).
* **Interface :** `Streamlit` pour le dashboarding temps réel.
* **Analyse :** `NumPy` pour les calculs de dérive de prix et scoring Alpha.

---

## ⚖️ Gouvernance et Conformité

Le système est conçu pour simuler les exigences des régulateurs financiers :
* **Surveillance du Marché :** Détection du Wash Trading et de la manipulation de prix.
* **Reporting :** Historique complet des exécutions pour auditabilité totale.