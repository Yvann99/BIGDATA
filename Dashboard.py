import streamlit as st
import pandas as pd
import os
import json
import time

# Configuration de la page Streamlit
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

def get_inventory(df):
    """Calcule la position nette (Inventaire) du trader manuel."""
    inventory = {p: 0 for p in COMMODITIES}
    if df.empty:
        return inventory
    
    # On filtre uniquement nos ordres passés via l'interface
    my_df = df[df['trader_id'] == 'MANUAL_CLIENT']
    
    for p in COMMODITIES:
        buys = my_df[(my_df['product'] == p) & (my_df['side'] == 'BUY')]['quantity'].sum()
        sells = my_df[(my_df['product'] == p) & (my_df['side'] == 'SELL')]['quantity'].sum()
        inventory[p] = int(buys - sells)
    return inventory

# --- CHARGEMENT DU BLOTTER ---
df_trades = load_trade_data()

# --- SIDEBAR : SÉLECTION DU PROFIL (PERSONA) ---
st.sidebar.image("https://img.icons8.com/fluent/96/000000/financial-analytics.png", width=60)
st.sidebar.title("LiquidityHub")
st.sidebar.subheader("Navigation")

profil = st.sidebar.selectbox(
    "👤 Choisissez votre rôle :",
    ["Trader Client", "Market Maker Promu (LP)", "Opérateur Business"]
)

st.sidebar.markdown("---")

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
                "trader_id": "MANUAL_CLIENT"
            }
            # Écriture dans le bus de message JSON
            with open(PATH_JSON, 'a') as f:
                f.write(json.dumps(order_data) + '\n')
            st.sidebar.success(f"Ordre {side} {quantity} {product} transmis !")

# Bouton de rafraîchissement manuel de l'interface
if st.sidebar.button("🔄 Rafraîchir les données"):
    st.rerun()


# ==========================================
# VUE 1 : TRADER CLIENT
# ==========================================
if profil == "Trader Client":
    st.title("Tableau de Bord : Trader Individuel")
    st.markdown("Suivez vos ordres envoyés au marché et analysez votre performance algorithmique.")
    
    # KPIs personnels
    if not df_trades.empty:
        my_trades = df_trades[df_trades['trader_id'] == 'MANUAL_CLIENT']
        nb_my_trades = len(my_trades)
    else:
        nb_my_trades = 0
        
    col1, col2 = st.columns(2)
    col1.metric("Vos exécutions manuelles", f"{nb_my_trades} Trades")
    # Simulation de l'Alpha Score de la gouvernance
    col2.metric("Votre Alpha Score", "0.00045", delta="Proche promotion MM", delta_color="inverse")
    
    st.subheader("Vos exécutions")
    if nb_my_trades > 0:
        st.dataframe(my_trades[['trade_id', 'product', 'side', 'quantity', 'execution_price', 'timestamp']].sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Vous n'avez pas encore passé d'ordre de trading sur cette session.")


# ==========================================
# VUE 2 : MARKET MAKER PROMU (LP)
# ==========================================
elif profil == "Market Maker (LP)":
    st.title("Gestion de Teneur de Marché")
    st.markdown("Espace réservé aux fournisseurs de liquidité. Pilotez vos **expositions nets ** pour contrôler vos risques.")
    
    # Calcul des positions via l'historique Parquet
    inventory = get_inventory(df_trades)
    
    st.subheader("Gestion des Risques")
    cols = st.columns(5)
    for i, prod in enumerate(COMMODITIES):
        qty = inventory[prod]
        # Couleur dynamique selon l'exposition (Achat net, Vente net, Flat)
        if qty > 0:
            color_state = "normal"
        elif qty < 0:
            color_state = "inverse"
        else:
            color_state = "off"
            
        cols[i].metric(
            label=f"Position {prod}", 
            value=f"{qty} Unités", 
            delta="LONG (Achat)" if qty > 0 else ("SHORT (Vente)" if qty < 0 else "FLAT"),
            delta_color=color_state
        )
        
    st.markdown("---")
    st.subheader("Carnet de spreads en direct")
    st.caption("Visualisation de la fourchette de prix.")
    # Un petit tableau propre fictif montrant les spreads gérés par le profil
    mock_spreads = pd.DataFrame({
        "Produit": COMMODITIES,
        "Votre Spread Cible": ["0.05 %", "0.02 %", "0.08 %", "0.04 %", "0.06 %"],
        "Statut": ["Actif (CME)", "Actif (CME)", "Actif (CME)", "Actif (ICE)", "Actif (CBOT)"]
    })
    st.table(mock_spreads)


# ==========================================
# VUE 3 : OPÉRATEUR BUSINESS (MACRO)
# ==========================================
elif profil == "Opérateur Business":
    st.title("Tour de Contrôle Plateforme")
    st.markdown("Statistiques globales et métriques financières pour le pilotage")
    
    if not df_trades.empty:
        total_volume = df_trades['quantity'].sum()
        # Calcul du CA via la colonne de commissions accumulées
        total_revenue = df_trades['commission_earned'].sum() if 'commission_earned' in df_trades.columns else total_volume * 0.15
        total_transactions = len(df_trades)
    else:
        total_volume, total_revenue, total_transactions = 0, 0.0, 0

    # Section KPIs globaux
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Volume Global Échangé", f"{total_volume} unités")
    kpi2.metric("Chiffre d'Affaires Plateforme", f"{total_revenue:.2f} $", delta="Frais de commissions (0.02%)")
    kpi3.metric("Nombre de Trades Totaux", f"{total_transactions} tx")
    
    st.markdown("---")
    
    # Affichage du Grand livre global de la bourse
    st.subheader("Flux Temps Réel")
    if not df_trades.empty:
        st.dataframe(df_trades.sort_index(ascending=False), use_container_width=True)
    else:
        st.warning("En attente de transactions de la part du moteur de matching...")

# Auto-refresh de la page Streamlit toutes les 2 secondes pour fluidifier la démo
time.sleep(2)
st.rerun()