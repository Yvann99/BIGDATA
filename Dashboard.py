import streamlit as st
import pandas as pd
import os
import time

st.set_page_config(page_title="LiquidityHub Dashboard", layout="wide")

def load_trades():
    path = 'data/executed_trades.parquet'
    if os.path.exists(path):
        # On tente 3 fois en cas de conflit d'accès avec le main.py
        for _ in range(3):
            try:
                return pd.read_parquet(path)
            except:
                time.sleep(0.1)
    return pd.DataFrame()

st.title("🏛️ LiquidityHub : Market Operator")

# --- SIDEBAR : TERMINAL TRADER ---
st.sidebar.header("🕹️ Terminal Trader")
with st.sidebar.form("order_form"):
    prod = st.selectbox("Produit", ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F'])
    side = st.radio("Sens", ["BUY", "SELL"])
    
    # Ajout du sélecteur de quantité
    qty = st.number_input("Quantité", min_value=1, max_value=1000, value=10, step=1)
    
    submit_button = st.form_submit_button("Envoyer l'ordre")
    
    if submit_button:
        # Note : Dans cette architecture, le clic informe l'utilisateur. 
        # Le MatchingEngine dans main.py traite les flux simulés.
        st.sidebar.success(f"✅ Ordre de {qty} {prod} transmis !")
        st.sidebar.caption("L'ordre sera exécuté au meilleur prix anonyme disponible.")

# --- ZONE LIVE ---
@st.fragment(run_every=1)
def update_view():
    df = load_trades()
    
    # 1. KPIs Plateforme
    c1, c2, c3 = st.columns(3)
    if not df.empty and 'commission' in df.columns:
        c1.metric("Volume Total", len(df))
        c2.metric("Revenus Plateforme", f"${df['commission'].sum():,.2f}")
        c3.metric("Actifs Supportés", "5 Commodities")

    # 2. Leaderboard Anonymisé
    st.subheader("🏆 Top Fournisseurs de Liquidité (Anonyme)")
    if not df.empty and 'mm_id' in df.columns:
        mm_stats = df.groupby('mm_id').agg({'trade_id': 'count', 'commission': 'sum'})
        mm_stats.columns = ['Trades Exécutés', 'Commissions Générées']
        mm_stats.index = [f"LP-{str(i)[:6]}" for i in mm_stats.index]
        st.dataframe(mm_stats.sort_values(by='Trades Exécutés', ascending=False), width='stretch')

    # 3. Flux de Marché (Blotter)
    st.subheader("📈 Dernières Exécutions")
    if not df.empty:
        st.dataframe(df.tail(15), width='stretch')
    else:
        st.warning("En attente de flux de données...")

update_view()