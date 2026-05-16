import streamlit as st
import pandas as pd
import os
import json
import time

st.set_page_config(page_title=" LiquidityHub", layout="wide", initial_sidebar_state="expanded")

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

# Extraction dynamique des prix de l'API
prices_live = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}
mm_leaderboard_data = []

if not df_trades.empty:
    for p in COMMODITIES:
        if f"ref_price_{p}" in df_trades.columns:
            prices_live[p] = float(df_trades[f"ref_price_{p}"].iloc[-1])
        
        # Récupération des prix des teneurs de marché depuis le Parquet
        if f"mm_id_{p}" in df_trades.columns and df_trades[f"mm_id_{p}"].iloc[-1] != "N/A":
            mm_leaderboard_data.append({
                "Market Maker": df_trades[f"mm_id_{p}"].iloc[-1],
                "Actif": p,
                "Prix Bid (Achat)": f"{df_trades[f'mm_bid_{p}'].iloc[-1]:.3f} $",
                "Prix Ask (Vente)": f"{df_trades[f'mm_ask_{p}'].iloc[-1]:.3f} $",
                "Volume disponible": int(df_trades[f"mm_vol_{p}"].iloc[-1])
            })

def get_portfolio_metrics(df, current_prices):
    metrics = {p: {"qty": 0, "pnl_realized": 0.0, "pnl_latent": 0.0, "total_buy_cash": 0.0, "total_sell_cash": 0.0, "buy_qty": 0, "sell_qty": 0} for p in COMMODITIES}
    if df.empty: return metrics
    my_trades = df[df['trader_id'] == 'MANUAL_CLIENT']
    for _, t in my_trades.iterrows():
        p = t['product']
        side = t['side']
        q = int(t['quantity'])
        px = float(t['execution_price'])
        if side == 'BUY':
            metrics[p]['qty'] += q
            metrics[p]['buy_qty'] += q
            metrics[p]['total_buy_cash'] += (q * px)
        else:
            metrics[p]['qty'] -= q
            metrics[p]['sell_qty'] += q
            metrics[p]['total_sell_cash'] += (q * px)
    for p in COMMODITIES:
        m = metrics[p]
        matched_qty = min(m['buy_qty'], m['sell_qty'])
        if matched_qty > 0:
            m['pnl_realized'] = matched_qty * ((m['total_sell_cash'] / m['sell_qty']) - (m['total_buy_cash'] / m['buy_qty']))
        live_px = current_prices[p]
        if m['qty'] > 0:
            m['pnl_latent'] = m['qty'] * (live_px - (m['total_buy_cash'] / m['buy_qty']))
        elif m['qty'] < 0:
            m['pnl_latent'] = abs(m['qty']) * ((m['total_sell_cash'] / m['sell_qty']) - live_px)
    return metrics

# --- SIDEBAR NAV ---
st.sidebar.image("https://img.icons8.com/fluent/96/000000/financial-analytics.png", width=60)
st.sidebar.title("LiquidityHub")
st.sidebar.subheader("Navigation")

profil = st.sidebar.selectbox(
    "👤 Choisissez votre rôle :",
    ["Trader Client", "Market Maker Promu (LP)", "Opérateur Business"]
)
st.sidebar.markdown("---")

# Ticker global en haut
st.markdown("### 🌐 Cours de Référence API Finance (Live CME)")
tick_cols = st.columns(5)
for idx, p in enumerate(COMMODITIES):
    tick_cols[idx].metric(label=p, value=f"{prices_live[p]:.2f} $")
st.markdown("---")

if profil == "Trader Client":
    st.sidebar.subheader("🕹️ Terminal de Trading")
    with st.sidebar.form(key='order_form', clear_on_submit=True):
        product = st.selectbox("Actif (Commodity)", COMMODITIES)
        side = st.radio("Sens de l'ordre", ["BUY", "SELL"])
        quantity = st.number_input("Quantité", min_value=1, max_value=100, value=1)
        if st.form_submit_button(label="🚀 Envoyer l'ordre"):
            with open(PATH_JSON, 'a') as f:
                f.write(json.dumps({"product": product, "side": side, "quantity": int(quantity), "trader_id": "MANUAL_CLIENT", "type": "ORDER"}) + '\n')
            st.sidebar.success(f"Ordre {side} {quantity} {product} transmis !")
            time.sleep(0.2)
            st.rerun()

if st.sidebar.button("🔄 Rafraîchir les données"):
    st.rerun()

# ==========================================
# VUE 1 : TRADER CLIENT
# ==========================================
if profil == "Trader Client":
    st.title("Tableau de Bord : Trader Individuel")
    st.markdown("Suivez vos ordres envoyés au marché et analysez votre performance algorithmique.")
    nb_my_trades = len(df_trades[df_trades['trader_id'] == 'MANUAL_CLIENT']) if not df_trades.empty else 0
    col1, col2 = st.columns(2)
    col1.metric("Vos exécutions manuelles", f"{nb_my_trades} Trades")
    col2.metric("Votre Alpha Score", "0.00045", delta="Proche promotion MM", delta_color="inverse")
    
    st.subheader("Vos exécutions")
    if nb_my_trades > 0:
        st.dataframe(df_trades[df_trades['trader_id'] == 'MANUAL_CLIENT'][['trade_id', 'product', 'side', 'quantity', 'execution_price', 'timestamp']].sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Vous n'avez pas encore passé d'ordre de trading sur cette session.")

# ==========================================
# VUE 2 : MARKET MAKER PROMU (LP)
# ==========================================
elif profil == "Market Maker Promu (LP)":
    st.title("Gestion de Teneur de Marché")
    st.markdown("Espace réservé aux fournisseurs de liquidité. Pilotez vos **expositions nets ** pour contrôler vos risques.")
    portfolio = get_portfolio_metrics(df_trades, prices_live)
    
    st.subheader("Gestion des Risques")
    cols = st.columns(5)
    for i, prod in enumerate(COMMODITIES):
        p_data = portfolio[prod]
        tot_pnl = p_data['pnl_realized'] + p_data['pnl_latent']
        cols[i].metric(
            label=f"Position {prod}", 
            value=f"{p_data['qty']} Unités", 
            delta=f"PnL: {tot_pnl:.2f} $",
            delta_color="normal" if p_data['qty'] >= 0 else "inverse"
        )
    st.markdown("---")
    
    col_input1, col_input2 = st.columns([1, 2])
    with col_input1:
        st.subheader("⚡ Injecter vos Quotes")
        mm_prod = st.selectbox("Actif à côter", COMMODITIES)
        ref_px = prices_live[mm_prod]
        target_spread_pct = st.slider("Spread ciblé (%)", min_value=0.01, max_value=1.0, value=0.1, step=0.01)
        calculated_spread = ref_px * (target_spread_pct / 100.0)
        mm_bid = st.number_input("Votre Prix Bid (Achat)", value=round(ref_px - (calculated_spread / 2), 3), format="%.3f")
        mm_ask = st.number_input("Votre Prix Ask (Vente)", value=round(ref_px + (calculated_spread / 2), 3), format="%.3f")
        mm_vol = st.number_input("Volume à injecter", min_value=10, max_value=1000, value=100, step=10)
        
        if st.button("🔥 Diffuser la Quote"):
            with open(PATH_JSON, 'a') as f:
                f.write(json.dumps({"product": mm_prod, "bid_price": float(mm_bid), "ask_price": float(mm_ask), "volume": int(mm_vol), "trader_id": "MANUAL_CLIENT", "type": "QUOTE_MM"}) + '\n')
            st.success(f"Quote diffusée pour {mm_prod} !")
            time.sleep(0.2)
            st.rerun()
            
    with col_input2:
        st.subheader("Carnet de spreads en direct")
        st.caption("Visualisation de la fourchette de prix.")
        if mm_leaderboard_data:
            st.table(pd.DataFrame(mm_leaderboard_data))
        else:
            st.info("Aucune quote active sur le marché.")

# ==========================================
# VUE 3 : OPÉRATEUR BUSINESS
# ==========================================
elif profil == "Opérateur Business":
    st.title("Tour de Contrôle Plateforme")
    st.markdown("Statistiques globales et métriques financières pour le pilotage")
    
    if not df_trades.empty:
        total_volume = int(df_trades['quantity'].sum())
        total_transactions = len(df_trades)
        
        # Calcul exact basé sur le volume de cash brassé * taux de commission (0.02%)
        cash_volume = (df_trades['quantity'] * df_trades['execution_price']).sum()
        total_revenue = cash_volume * 0.0002
    else:
        total_volume, total_revenue, total_transactions = 0, 0.0, 0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Volume Global Échangé", f"{total_volume} unités")
    kpi2.metric("Bénéfice des Commissions (CA)", f"{total_revenue:.2f} $", delta="0.02 % par trade")
    kpi3.metric("Nombre de Trades Totaux", f"{total_transactions} tx")
    
    st.markdown("---")
    
    col_table1, col_table2 = st.columns([1, 1])
    
    with col_table1:
        st.subheader(" Classement des Meilleurs Market Makers (LPs)")
        if mm_leaderboard_data:
            st.dataframe(pd.DataFrame(mm_leaderboard_data), use_container_width=True, hide_index=True)
        else:
            st.info("En attente de cotations des teneurs de marchés...")
            
    with col_table2:
        st.subheader("Flux Temps Réel")
        if not df_trades.empty:
            # On affiche TOUS les colonnes originales pour voir les bots et le client manuel mélangés
            st.dataframe(df_trades[['trade_id', 'product', 'side', 'quantity', 'execution_price', 'trader_id', 'timestamp']].sort_index(ascending=False), use_container_width=True)
        else:
            st.warning("En attente de transactions de la part du moteur...")

time.sleep(1.0)
st.rerun()