import streamlit as st
import pandas as pd
import time
import os

# Configuration de la page
st.set_page_config(page_title="Commodity Trading Desk", layout="wide")

st.title("Market Maker Dashboard - Commodities")

# 1. Chargement des donnees (Etape 3 & 4)
def load_data():
    if os.path.exists('data/executed_trades.parquet'):
        return pd.read_parquet('data/executed_trades.parquet')
    return pd.DataFrame()

df_trades = load_data()

# Barre latérale pour passer un ordre (Etape 5)
st.sidebar.header("Passer un Ordre Manuel")
with st.sidebar.form("order_form"):
    product = st.selectbox("Produit", ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F'])
    quantity = st.number_input("Quantite", min_value=1, value=10)
    side = st.radio("Sens", ["BUY", "SELL"])
    submit = st.form_submit_button("Envoyer l'ordre")
    
    if submit:
        st.sidebar.success(f"Ordre {side} de {quantity} {product} envoye !")
        # Ici, dans une version complete, on injecterait cet ordre dans la queue asyncio

# 2. Affichage des indicateurs cles (KPIs)
col1, col2, col3 = st.columns(3)

if not df_trades.empty:
    total_trades = len(df_trades)
    avg_spread = df_trades['spread_applied'].mean()
    
    col1.metric("Total Trades", total_trades)
    col2.metric("Spread Moyen", f"{avg_spread:.4%}")
    col3.metric("Statut Engine", "RUNNING", delta="Live")

    # 3. Visualisation du Trading Book
    st.subheader("Positions Actuelles et Inventaire")
    # On recalcule l'inventaire a la volee pour le dashboard
    inventory = df_trades.groupby('product').apply(
        lambda x: x[x['side'] == 'SELL']['quantity'].sum() - x[x['side'] == 'BUY']['quantity'].sum()
    )
    st.bar_chart(inventory)

    # 4. Historique des transactions
    st.subheader("Dernieres Executions")
    st.dataframe(df_trades.tail(10), use_container_width=True)
else:
    st.info("Aucune donnee de trading detectee. Lancez main.py pour generer des flux.")

# Rafraichissement automatique
time.sleep(2)
if st.checkbox("Auto-refresh"):
    st.rerun()