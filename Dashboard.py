import streamlit as st
import pandas as pd
import os
import json
import time

# Configuration de la page Streamlit (Conserve ton titre exact)
st.set_page_config(page_title=" LiquidityHub", layout="wide", initial_sidebar_state="expanded")

# --- PARAMÈTRES ET CHEMINS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_PARQUET = os.path.join(BASE_DIR, 'data', 'executed_trades.parquet')
PATH_JSON = os.path.join(BASE_DIR, 'data', 'pending_orders.json')
COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']

# --- FONCTIONS REQUISES ---
def load_trade_data():
    """Charge le fichier historique Parquet généré par le moteur."""
    if os.path.exists(PATH_PARQUET):
        try:
            return pd.read_parquet(PATH_PARQUET)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# Chargement initial des données pour extraire les prix de l'API transmis par le moteur
df_trades = load_trade_data()

# Dictionnaire de prix par défaut (mis à jour dynamiquement via le Parquet)
prices_live = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}
if not df_trades.empty:
    for p in COMMODITIES:
        col_name = f"ref_price_{p}"
        if col_name in df_trades.columns:
            prices_live[p] = float(df_trades[col_name].iloc[-1])

def get_portfolio_metrics(df, current_prices):
    """Calcule l'inventaire, le PnL Réalisé et le PnL Latent (Mark-to-Market)."""
    metrics = {p: {"qty": 0, "pnl_realized": 0.0, "pnl_latent": 0.0, "total_buy_cash": 0.0, "total_sell_cash": 0.0, "buy_qty": 0, "sell_qty": 0} for p in COMMODITIES}
    
    if df.empty:
        return metrics
        
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
        # Calcul du PnL réalisé sur les paires matchées
        matched_qty = min(m['buy_qty'], m['sell_qty'])
        if matched_qty > 0:
            vwap_b = m['total_buy_cash'] / m['buy_qty']
            vwap_s = m['total_sell_cash'] / m['sell_qty']
            m['pnl_realized'] = matched_qty * (vwap_s - vwap_b)
            
        # Calcul du PnL Latent (basé sur le prix live de l'API)
        live_px = current_prices[p]
        if m['qty'] > 0: # Long
            vwap_buy = m['total_buy_cash'] / m['buy_qty']
            m['pnl_latent'] = m['qty'] * (live_px - vwap_buy)
        elif m['qty'] < 0: # Short
            vwap_sell = m['total_sell_cash'] / m['sell_qty']
            m['pnl_latent'] = abs(m['qty']) * (vwap_sell - live_px)
        else:
            m['pnl_latent'] = 0.0
            
    return metrics

# --- SIDEBAR : SÉLECTION DU PROFIL (PERSONA) ---
st.sidebar.image("https://img.icons8.com/fluent/96/000000/financial-analytics.png", width=60)
st.sidebar.title("LiquidityHub")
st.sidebar.subheader("Navigation")

# Garde tes rôles exacts d'origine
profil = st.sidebar.selectbox(
    "👤 Choisissez votre rôle :",
    ["Trader Client", "Market Maker Promu (LP)", "Opérateur Business"]
)

st.sidebar.markdown("---")

# --- TICKER DE PRIX UNIVERSEL (Visible par le Trader et le MM) ---
st.markdown("### 🌐 Cours de Référence API Finance (Live CME)")
tick_cols = st.columns(5)
for idx, p in enumerate(COMMODITIES):
    tick_cols[idx].metric(label=p, value=f"{prices_live[p]:.2f} $")
st.markdown("---")

# --- FORMULAIRE DE PASSAGE D'ORDRE (Uniquement visible pour le Trader) ---
if profil == "Trader Client":
    st.sidebar.subheader("🕹️ Terminal de Trading")
    with st.sidebar.form(key='order_form', clear_on_submit=True):
        product = st.selectbox("Actif (Commodity)", COMMODITIES)
        side = st.radio("Sens de l'ordre", ["BUY", "SELL"])
        quantity = st.number_input("Quantité", min_value=1, max_value=100, value=1)
        submit_button = st.form_submit_button(label="🚀 Envoyer l'ordre")
        
        if submit_button:
            order_data = {
                "product": product,
                "side": side,
                "quantity": int(quantity),
                "trader_id": "MANUAL_CLIENT",
                "type": "ORDER"
            }
            with open(PATH_JSON, 'a') as f:
                f.write(json.dumps(order_data) + '\n')
            st.sidebar.success(f"Ordre {side} {quantity} {product} transmis !")
            time.sleep(0.2)
            st.rerun()

# Bouton de rafraîchissement manuel de l'interface
if st.sidebar.button("🔄 Rafraîchir les données"):
    st.rerun()


# ==========================================
# VUE 1 : TRADER CLIENT
# ==========================================
if profil == "Trader Client":
    st.title("Tableau de Bord : Trader Individuel")  # Ton titre exact
    st.markdown("Suivez vos ordres envoyés au marché et analysez votre performance algorithmique.")
    
    # KPIs personnels
    if not df_trades.empty:
        my_trades = df_trades[df_trades['trader_id'] == 'MANUAL_CLIENT']
        nb_my_trades = len(my_trades)
    else:
        nb_my_trades = 0
        
    col1, col2 = st.columns(2)
    col1.metric("Vos exécutions manuelles", f"{nb_my_trades} Trades")
    col2.metric("Votre Alpha Score", "0.00045", delta="Proche promotion MM", delta_color="inverse")
    
    st.subheader("Vos exécutions")  # Ton titre exact
    if nb_my_trades > 0:
        st.dataframe(my_trades[['trade_id', 'product', 'side', 'quantity', 'execution_price', 'timestamp']].sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Vous n'avez pas encore passé d'ordre de trading sur cette session.")


# ==========================================
# VUE 2 : MARKET MAKER PROMU (LP)
# ==========================================
elif profil == "Market Maker Promu (LP)":
    st.title("Gestion de Teneur de Marché")  # Ton titre exact
    st.markdown("Espace réservé aux fournisseurs de liquidité. Pilotez vos **expositions nets ** pour contrôler vos risques.")
    
    # Calcul complet du Portefeuille (Inventaire, PnL Latent et Réalisé)
    portfolio = get_portfolio_metrics(df_trades, prices_live)
    
    st.subheader("Gestion des Risques")  # Ton titre exact
    cols = st.columns(5)
    for i, prod in enumerate(COMMODITIES):
        p_data = portfolio[prod]
        qty = p_data['qty']
        tot_pnl = p_data['pnl_realized'] + p_data['pnl_latent']
        
        if qty > 0:
            color_state = "normal"
        elif qty < 0:
            color_state = "inverse"
        else:
            color_state = "off"
            
        # Métrique enrichie : Affiche la position nette et le PnL global/latent juste en dessous
        cols[i].metric(
            label=f"Position {prod}", 
            value=f"{qty} Unités", 
            delta=f"PnL: {tot_pnl:.2f} $ (Latent: {p_data['pnl_latent']:.1f}$)",
            delta_color=color_state
        )
        
    st.markdown("---")
    
    # --- FORMULAIRE D'INJECTION DE QUOTES POUR LE MARKET MAKER ---
    col_input1, col_input2 = st.columns([1, 2])
    with col_input1:
        st.subheader("⚡ Injecter vos Quotes")
        mm_prod = st.selectbox("Actif à côter", COMMODITIES)
        ref_px = prices_live[mm_prod]
        
        st.caption(f"Prix API de référence : **{ref_px:.2f} $**")
        
        # Slider pour que le MM ajuste son spread cible en direct
        target_spread_pct = st.slider("Spread ciblé (%)", min_value=0.01, max_value=1.0, value=0.1, step=0.01)
        calculated_spread = ref_px * (target_spread_pct / 100.0)
        
        suggested_bid = round(ref_px - (calculated_spread / 2), 3)
        suggested_ask = round(ref_px + (calculated_spread / 2), 3)
        
        mm_bid = st.number_input("Votre Prix Bid (Achat)", value=suggested_bid, format="%.3f")
        mm_ask = st.number_input("Votre Prix Ask (Vente)", value=suggested_ask, format="%.3f")
        mm_vol = st.number_input("Volume à injecter", min_value=10, max_value=1000, value=100, step=10)
        
        if st.button("🔥 Diffuser la Quote"):
            quote_data = {
                "product": mm_prod,
                "bid_price": float(mm_bid),
                "ask_price": float(mm_ask),
                "volume": int(mm_vol),
                "trader_id": "MANUAL_CLIENT",
                "type": "QUOTE_MM"
            }
            with open(PATH_JSON, 'a') as f:
                f.write(json.dumps(quote_data) + '\n')
            st.success(f"Quote diffusée pour {mm_prod} !")
            time.sleep(0.2)
            st.rerun()
            
    with col_input2:
        st.subheader("Carnet de spreads en direct")  # Ton titre exact
        st.caption("Visualisation de la fourchette de prix.")  # Ta description exacte
        
        mock_spreads = pd.DataFrame({
            "Produit": COMMODITIES,
            "Votre Spread Cible": [f"{0.05 if p != mm_prod else target_spread_pct} %" for p in COMMODITIES],
            "Statut": ["Actif (CME)", "Actif (CME)", "Actif (CME)", "Actif (ICE)", "Actif (CBOT)"]
        })
        st.table(mock_spreads)


# ==========================================
# VUE 3 : OPÉRATEUR BUSINESS (MACRO)
# ==========================================
elif profil == "Opérateur Business":
    st.title("Tour de Contrôle Plateforme")  # Ton titre exact
    st.markdown("Statistiques globales et métriques financières pour le pilotage")  # Ta description exacte
    
    if not df_trades.empty:
        total_volume = df_trades['quantity'].sum()
        total_revenue = df_trades['commission_earned'].sum() if 'commission_earned' in df_trades.columns else total_volume * 0.15
        total_transactions = len(df_trades)
    else:
        total_volume, total_revenue, total_transactions = 0, 0.0, 0

    # Section KPIs globaux (Garde tes intitulés exacts)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Volume Global Échangé", f"{total_volume} unités")
    kpi2.metric("Chiffre d'Affaires Plateforme", f"{total_revenue:.2f} $", delta="Frais de commissions (0.02%)")
    kpi3.metric("Nombre de Trades Totaux", f"{total_transactions} tx")
    
    st.markdown("---")
    
    # Affichage du Grand livre global de la bourse
    st.subheader("Flux Temps Réel")  # Ton titre exact
    if not df_trades.empty:
        st.dataframe(df_trades.sort_index(ascending=False), use_container_width=True)
    else:
        st.warning("En attente de transactions de la part du moteur de matching...")

# Rafraîchissement automatique
time.sleep(1.5)
st.rerun()