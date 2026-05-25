import asyncio
import random
import pandas as pd
import os
import json
import yfinance as yf

COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']
NB_CANDIDATES = 15  # 15 robots simulant des candidats au challenge de la Prop Firm

current_market_prices = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}

from MarketTypes import Order, Trade, Quote, Side, Role, TraderProfile
from MatchingEngine import MatchingEngine
from Governance import Governance

async def fetch_api_prices_task():
    """Tâche de fond indépendante : met à jour les prix réels du marché mondial."""
    global current_market_prices
    fallback = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}
    
    while True:
        for p in COMMODITIES:
            try:
                async with asyncio.timeout(2.0):
                    ticker = yf.Ticker(p)
                    price = await asyncio.to_thread(lambda: ticker.fast_info.get('last_price', None))
                    
                    if price and price > 0:
                        current_market_prices[p] = round(float(price), 3)
                    else:
                        current_market_prices[p] = fallback.get(p, 100.0)
            except (TimeoutError, Exception):
                current_market_prices[p] = fallback.get(p, 100.0)
                
        await asyncio.sleep(10.0)

async def institutional_liquidity_provider(mm_id, engine, product):
    """Simule le flux de contrepartie (BFI/Carnet) pour que les candidats puissent trader."""
    while True:
        base_price = current_market_prices.get(product, 100.0)
        spread = base_price * 0.0005  # Spread institutionnel serré
        quote = Quote(
            mm_id=mm_id, product=product,
            bid_price=round(base_price - (spread/2), 3),
            ask_price=round(base_price + (spread/2), 3),
            bid_volume=random.randint(500, 2000), # Profondeur de carnet importante
            ask_volume=random.randint(500, 2000)
        )
        engine.update_quote(quote)
        await asyncio.sleep(1.0)

async def candidate_worker(trader_id, engine, governance):
    """Simule un candidat au challenge envoyant des ordres pour tenter de se faire financer."""
    while True:
        product = random.choice(COMMODITIES)
        side = random.choice([Side.BUY, Side.SELL])
        order = Order(product=product, side=side, quantity=random.randint(1, 10), trader_id=trader_id)
        
        trade = await engine.match_order(order)
        if trade:
            # On simule une évolution court terme du marché pour calculer l'Alpha Score (Edge)
            future_mid = trade.execution_price * random.uniform(0.999, 1.001)
            governance.update_trader_stats(trade, future_mid)
            
        await asyncio.sleep(random.uniform(0.2, 0.8))

async def check_manual_orders(engine, governance):
    """Consomme les ordres du ticket d'ordre Streamlit (Candidat Humain)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, 'data', 'pending_orders.json')
    
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return

    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        
        with open(path, 'w') as f:
            f.truncate()
            
        for line in lines:
            if not line.strip(): 
                continue
            data = json.loads(line)
            
            order = Order(
                product=data['product'], side=Side.BUY if data['side'] == "BUY" else Side.SELL,
                quantity=data['quantity'], trader_id=data['trader_id']
            )
            trade = await engine.match_order(order, price_limit=None)
            if trade:
                # Évaluation immédiate du trade manuel par le Risk Management
                governance.update_trader_stats(trade, trade.execution_price)
                print(f"🤝 [CHALLENGE LIVE] Ordre candidat exécuté à {trade.execution_price}$ !")
                
    except Exception as e:
        print(f"⚠️ Erreur traitement flux manuel : {e}")

async def main_orchestrator():
    if not os.path.exists('data'): os.makedirs('data')
    
    engine = MatchingEngine(commission_rate=0.0002) # Commissions de courtage simulées
    gov = Governance(target_alpha=0.0001, min_trades=15, max_drawdown_pct=0.05)
    
    print("\n" + "="*60)
    print("🚀 FINISTECH PROP FIRM ENGINE INITIALIZATION... 🚀")
    print("="*60)
    print("⚙️  [1/3] Environnement de simulation asynchrone prêt.")
    print("🌐 [2/3] Flux de prix internationaux connectés (CME Group Live).")
    print(f"👥 [3/3] Déploiement de {NB_CANDIDATES} robots en phase d'évaluation.")
    print("-"*60)
    print("🟢 PLATEFORME DE CHALLENGE OUVERTE : En attente de détection d'Alpha...")
    print("="*60 + "\n")

    api_task = asyncio.create_task(fetch_api_prices_task())

    # Injection de la liquidité institutionnelle globale (carnet de la Prop Firm)
    mm_tasks = [asyncio.create_task(institutional_liquidity_provider(f"LP_INSTITUTIONAL_{p}", engine, p)) for p in COMMODITIES]
    # Lancement des robots candidats
    candidate_tasks = [asyncio.create_task(candidate_worker(f"Robot_Candidate_{i}", engine, gov)) for i in range(NB_CANDIDATES)]

    try:
        while True:
            await check_manual_orders(engine, gov)
            
            # Évaluation des comptes pour détection des réussites du challenge
            new_funded_traders = gov.evaluate_promotions()
            for t_id in new_funded_traders:
                print(f"✨ [PROMOTION] {t_id} a validé ses métriques de risque et d'Alpha ! Passage au statut FUNDED TRADER.")
            
            # Sauvegarde colonnaire Big Data pour le Dashboard
            if engine.trade_history:
                trades_dicts = [vars(t).copy() for t in engine.trade_history]
                for t in trades_dicts:
                    if isinstance(t['side'], Side): 
                        t['side'] = t['side'].value
                
                df = pd.DataFrame(trades_dicts)
                df.to_parquet('data/executed_trades.parquet.tmp', index=False)
                os.replace('data/executed_trades.parquet.tmp', 'data/executed_trades.parquet')
                
                # Enrichissement pour l'IHM
                df_dash = df.copy()
                for p in COMMODITIES:
                    df_dash[f"ref_price_{p}"] = current_market_prices[p]
                
                df_dash.to_parquet('data/dashboard_trades.parquet.tmp', index=False)
                os.replace('data/dashboard_trades.parquet.tmp', 'data/dashboard_trades.parquet')
            
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"💥 Erreur critique du moteur : {e}")
    finally:
        api_task.cancel()
        for t in mm_tasks + candidate_tasks: t.cancel()
        print("\n🛑 Engine Finistech arrêté proprement.")

if __name__ == "__main__":
    asyncio.run(main_orchestrator())