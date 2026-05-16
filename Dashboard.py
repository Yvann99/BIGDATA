import streamlit as st
import pandas as pd
import os
import time
import json

st.set_page_config(page_title="LiquidityHub Dashboard", layout="wide")

# --- CHARGEMENT DES DONNÉES ---

def load_trades():
    """Lit l'historique des trades exécutés (Parquet)."""
    path = 'data/executed_trades.parquet'
    if os.path.exists(path):
        for _ in range(3):
            try:
                return pd.read_parquet(path)
            except:
                time.sleep(0.1)
    return pd.DataFrame()

def load_pending_orders():
    """Lit la file d'attente des ordres en attente de traitement (JSON)."""
    path = 'data/pending_orders.json'
    if os.path.exists(path) and os.path.getsize(path) > 0:
        for _ in range(3):
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
                orders = [json.loads(line) for line in lines if line.strip()]
                return pd.DataFrame(orders)
            except:
                time.sleep(0.1)
    return pd.DataFrame()

# --- INTERFACE OPÉRATEUR ---

st.title("🏛️ LiquidityHub : Market Operator")

# --- SIDEBAR : TERMINAL TRADER (PASSAGE D'ORDRE CLIENT) ---
st.sidebar.header("🕹️ Terminal Trader")
with st.sidebar.form("order_form"):
    prod = st.selectbox("Produit", ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F'])
    side = st.radio("Sens", ["BUY", "SELL"])
    qty = st.number_input("Quantité", min_value=1, max_value=1000, value=10, step=1)
    
    # AJOUT : Saisie du Prix Limite par le client
    price = st.number_input("Prix Limite ($)", min_value=0.0, value=100.0, step=0.1)
    
    submit_button = st.form_submit_button("Envoyer l'ordre")
    
    if submit_button:
        # Création de l'objet d'ordre pour la file d'attente
        new_order = {
            "product": prod,
            "side": side,
            "quantity": int(qty),
            "price": float(price),
            "trader_id": "MANUAL_CLIENT",
            "timestamp": time.strftime('%H:%M:%S', time.localtime()),
            "status": "En attente"
        }
        
        # Écriture asynchrone dans le bus de transit JSON
        os.makedirs('data', exist_ok=True)
        with open('data/pending_orders.json', 'a') as f:
            f.write(json.dumps(new_order) + "\n")
            
        st.sidebar.success(f"✅ Ordre de {qty} {prod} à {price}$ transmis !")

# --- ZONE LIVE VIEW (RAFRAÎCHISSEMENT HAUTE FRÉQUENCE) ---
@st.fragment(run_every=1)
def update_view():
    df_executed = load_trades()
    df_pending = load_pending_orders()
    
    # 1. ÉCRAN DES TOP PRIX DU MARCHÉ (Anonymisé pour éviter l'arbitrage)
    st.subheader("🌐 Top Prix Anonymes des Market Makers (Best Bid/Ask)")
    cols = st.columns(5)
    products = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']
    
    for i, p in enumerate(products):
        with cols[i]:
            # Filtrage des derniers trades pour simuler une cotation dynamique proche du marché
            if not df_executed.empty and p in df_executed['product'].values:
                last_price = df_executed[df_executed['product'] == p]['execution_price'].iloc[-1]
                bid = round(last_price * 0.999, 2)
                ask = round(last_price * 1.001, 2)
            else:
                # Prix par défaut si aucun trade n'a encore eu lieu
                bid, ask = 99.90, 100.10
                
            st.metric(label=p, value=f"Ask: {ask}", delta=f"Bid: {bid}", delta_color="normal")
            st.caption("Source: LP-Anonyme (Verified)")

    st.markdown("---")
    
    # 2. CONFIGURATION DES KPIS
    c1, c2, c3 = st.columns(3)
    if not df_executed.empty and 'commission' in df_executed.columns:
        c1.metric("Volume Total Exécuté", len(df_executed))
        c2.metric("Revenus Plateforme (Commissions)", f"${df_executed['commission'].sum():,.2f}")
        c3.metric("Actifs Supportés", "5 Commodities")
    else:
        c1.metric("Volume Total Exécuté", 0)
        c2.metric("Revenus Plateforme", "$0.00")
        c3.metric("Actifs Supportés", "5 Commodities")

    st.markdown("---")

    # 3. NOUVEAU : FLUX DYNAMIQUE DES ORDRES EN ATTENTE (Vision Client)
    st.subheader("⏳ Votre Flux d'Ordres en Attente (File d'attente Moteur)")
    if not df_pending.empty:
        # On filtre pour afficher les ordres du client manuel
        client_pending = df_pending[df_pending['trader_id'] == 'MANUAL_CLIENT']
        if not client_pending.empty:
            st.dataframe(
                client_pending[['timestamp', 'product', 'side', 'quantity', 'price', 'status']], 
                width='stretch', 
                hide_index=True
            )
        else:
            st.info("Aucun ordre personnel dans la file d'attente actuelle.")
    else:
        st.info("La file d'attente est vide. Tous les ordres ont été consommés par le moteur.")

    st.markdown("---")

    # 4. LEADERBOARD ANONYMISÉ
    st.subheader("🏆 Leaderboard Fournisseurs de Liquidité (Anonyme)")
    if not df_executed.empty and 'mm_id' in df_executed.columns:
        mm_stats = df_executed.groupby('mm_id').agg({'trade_id': 'count', 'commission': 'sum'})
        mm_stats.columns = ['Trades Exécutés', 'Commissions Générées']
        # Anonymisation stricte des LPs pour l'oral
        mm_stats.index = [f"LP-{str(i)[:6]}" for i in mm_stats.index]
        st.dataframe(mm_stats.sort_values(by='Trades Exécutés', ascending=False), width='stretch')

    # 5. BLOTTER GLOBAL
    st.subheader("📈 Dernières Exécutions Globales")
    if not df_executed.empty:
        st.dataframe(df_executed.tail(15), width='stretch', hide_index=True)
    else:
        st.warning("En attente de flux de données du moteur...")

update_view()