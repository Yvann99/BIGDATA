import streamlit as st
import pandas as pd
import os
import json
import time

st.set_page_config(page_title="Finistech Analytics", layout="wide", initial_sidebar_state="expanded")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_PARQUET = os.path.join(BASE_DIR, 'data', 'dashboard_trades.parquet')
PATH_JSON = os.path.join(BASE_DIR, 'data', 'pending_orders.json')
COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']

def load_trade_data():
    if os.path.exists(PATH_PARQUET):
        try:
            return pd.read_parquet(PATH_PARQUET)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

df_trades = load_trade_data()

# Extraction des derniers prix du marché mondial
prices_live = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}
if not df_trades.empty:
    for p in COMMODITIES:
        if f"ref_price_{p}" in df_trades.columns:
            prices_live[p] = float(df_trades[f"ref_price_{p}"].iloc[-1])

# --- DESIGN DE L'INTERFACE STREAMLIT ---
st.title("🦅 FINISTECH - Data-Driven Prop Trading Platform")
st.caption("Moteur d'évaluation quantitative de l'Alpha et gestion du risque à haute fréquence")

# Barre latérale : Gestion des profils métiers de la Prop Firm
st.sidebar.header("🕹️ Espace Profils Finistech")
user_profile = st.sidebar.selectbox(
    "Choisir votre vue de terminal :",
    ["Candidat au Challenge", "Prop Firm Risk Room (Backoffice)", "Espace Investisseurs"]
)

# Simulation dynamique des performances du candidat humain pour l'IHM
if 'my_pnl' not in st.session_state:
    st.session_state.my_pnl = 0.0
if 'my_trades_count' not in st.session_state:
    st.session_state.my_trades_count = 0

# ----------------------------------------------------
# VUE 1 : CANDIDAT AU CHALLENGE
# ----------------------------------------------------
if user_profile == "Candidat au Challenge":
    st.header("🎯 Tableau de Bord du Challenge")
    st.subheader("Prouvez votre Edge statistique. Évitez le Drawdown. Obtenez un financement de 500 000 $.")

    # KPIs du candidat actuel
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Balance Initiale", "100 000.00 $")
    
    # Calcul du Drawdown en direct
    current_balance = 100000.0 + st.session_state.my_pnl
    drawdown_pct = max(0.0, (100000.0 - current_balance) / 100000.0)
    
    c2.metric("PnL Réalisé (Challenge)", f"{st.session_state.my_pnl:.2f} $", 
              delta="Bénéficiaire" if st.session_state.my_pnl >= 0 else "Déficitaire")
    
    c3.metric("Règle de Max Drawdown", f"{drawdown_pct:.2%} / 5.00%", 
              delta="OK" if drawdown_pct < 0.05 else "ÉLIMINÉ", delta_color="inverse")
    
    c4.metric("Volume d'Évaluations", f"{st.session_state.my_trades_count} / 15 trades")

    st.markdown("---")

    # Ticket d'ordre interactif
    col_order, col_prices = st.columns([1, 2])
    with col_order:
        st.subheader("⚡ Ticket d'Ordre d'Évaluation")
        asset = st.selectbox("Sélectionner l'actif de commodité :", COMMODITIES)
        side_choice = st.radio("Sens de la position :", ["BUY (Long)", "SELL (Short)"])
        qty = st.number_input("Taille de lot (Quantité) :", min_value=1, max_value=50, value=5)
        
        if st.button("🚀 Soumettre l'ordre au Smart Order Router"):
            side_str = "BUY" if "BUY" in side_choice else "SELL"
            order_payload = {
                "product": asset,
                "side": side_str,
                "quantity": int(qty),
                "trader_id": "Candidat_Humain_01"
            }
            
            # Écriture dans le bus de messages JSON
            os.makedirs(os.path.dirname(PATH_JSON), exist_ok=True)
            with open(PATH_JSON, 'a') as f:
                f.write(json.dumps(order_payload) + "\n")
            
            # Simulation locale immédiate pour réactivité de l'IHM
            exec_p = prices_live[asset]
            sim_slippage = exec_p * 0.0001 if side_str == "BUY" else -exec_p * 0.0001
            sim_pnl = (sim_slippage * qty) * -1 # Impact fictif immédiat
            st.session_state.my_pnl += sim_pnl - (exec_p * qty * 0.0002)
            st.session_state.my_trades_count += 1
            
            st.success(f"Ordre transmis au carnet asynchrone ! Exécution estimée autour de : {exec_p} $")
            time.sleep(0.2)
            st.rerun()

    with col_prices:
        st.subheader("🌐 Prix de Référence du Marché de Contrepartie")
        df_prices = pd.DataFrame(list(prices_live.items()), columns=["Produit Matière Première", "Prix Spot Actuel ($)"])
        st.dataframe(df_prices, use_container_width=True, hide_index=True)

# ----------------------------------------------------
# VUE 2 : PROP FIRM RISK ROOM (BACKOFFICE)
# ----------------------------------------------------
elif user_profile == "Prop Firm Risk Room (Backoffice)":
    st.header("🎛️ Salle des Risques & Analyse Big Data")
    
    if not df_trades.empty:
        total_transactions = len(df_trades)
        cash_volume = (df_trades['quantity'] * df_trades['execution_price']).sum()
        # Chiffre d'affaires de la Prop firm généré par les micro-commissions de plateforme
        total_revenue = cash_volume * 0.0002 
    else:
        total_transactions, total_revenue = 0, 0.0

    k1, k2 = st.columns(2)
    k1.metric("Chiffre d'Affaires de la Plateforme (Commissions)", f"{total_revenue:.4f} $", delta="0.02 % par transaction")
    k2.metric("Activité du Simulateur (Trades Traités)", f"{total_transactions} ordres appariés")

    st.markdown("---")
    st.subheader("📊 Grand Livre des Transactions Global (Données Colonnaires .parquet)")
    
    if not df_trades.empty:
        # Tri pour voir les dernières données Big Data en haut
        st.dataframe(df_trades.sort_values(by='timestamp', ascending=False), use_container_width=True)
    else:
        st.info("Aucune donnée Parquet détectée. Veuillez démarrer le script 'main.py' pour injecter le flux.")

# ----------------------------------------------------
# VUE 3 : ESPACE INVESTISSEURS
# ----------------------------------------------------
else:
    st.header("🏆 Tableau des Talents Financés (Funded Leaderboard)")
    st.subheader("Sélection scientifique d'Alpha validée par notre modèle de Gouvernance Big Data")
    
    # Génération d'un leaderboard de démonstration fondé sur l'analyse de flux réels
    st.markdown("Ces traders ont complété les 15 trades minimum sans enfreindre la règle des 5% de Max Drawdown.")
    
    mock_leaderboard = [
        {"Identifiant Anonyme": "FT-9283a2", "Alpha Score (Points de Base)": "14.5 bps", "Profits Réalisés": "4 250.00 $", "Capital Alloué": "500 000 $", "Statut": "VÉRIFIÉ & ACTIF"},
        {"Identifiant Anonyme": "FT-1029c9", "Alpha Score (Points de Base)": "8.2 bps", "Profits Réalisés": "2 110.50 $", "Capital Alloué": "500 000 $", "Statut": "VÉRIFIÉ & ACTIF"},
        {"Identifiant Anonyme": "FT-5502b1", "Alpha Score (Points de Base)": "4.1 bps", "Profits Réalisés": "980.00 $", "Capital Alloué": "500 000 $", "Statut": "VÉRIFIÉ & ACTIF"},
    ]
    st.dataframe(pd.DataFrame(mock_leaderboard), use_container_width=True, hide_index=True)
    st.info("💡 Les investisseurs institutionnels peuvent utiliser ces métriques d'Alpha glissant pour allouer des fonds sur nos algorithmes de copy-trading répliqués.")

# Rafraîchissement automatique pour simuler le temps réel
time.sleep(1.0)
st.rerun()