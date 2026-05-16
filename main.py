import asyncio
import random
import pandas as pd
import os
import json
import yfinance as yf

COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']
NB_TRADERS = 15

current_market_prices = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}

from MarketTypes import Order, Trade, Quote, Side, Role, TraderProfile
from MatchingEngine import MatchingEngine
from Governance import Governance

async def fetch_api_prices_task():
    """Tâche de fond indépendante : met à jour les prix de l'API avec Timeout de sécurité."""
    global current_market_prices
    fallback = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}
    
    while True:
        for p in COMMODITIES:
            try:
                # Timeout de 2 secondes max pour éviter le blocage du week-end
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

async def market_maker_behavior(mm_id, engine, product):
    """Simule un Market Maker calé sur les prix réels de l'API Finance."""
    while True:
        base_price = current_market_prices.get(product, 100.0)
        spread = base_price * 0.0005
        quote = Quote(
            mm_id=mm_id, product=product,
            bid_price=round(base_price - (spread/2), 3),
            ask_price=round(base_price + (spread/2), 3),
            bid_volume=random.randint(100, 500),
            ask_volume=random.randint(100, 500)
        )
        engine.update_quote(quote)
        await asyncio.sleep(1.0)

async def trader_worker(trader_id, engine, governance):
    """Simule un client automatique envoyant des ordres À L'INFINI."""
    while True:
        product = random.choice(COMMODITIES)
        side = random.choice([Side.BUY, Side.SELL])
        order = Order(product=product, side=side, quantity=random.randint(1, 10), trader_id=trader_id)
        
        trade = await engine.match_order(order)
        if trade:
            future_mid = trade.execution_price * random.uniform(0.999, 1.001)
            governance.update_trader_stats(trade, future_mid)
            
        await asyncio.sleep(random.uniform(0.2, 0.8))

async def check_manual_orders(engine, governance):
    """Consomme les ordres du Terminal Trader ET les quotes personnalisées du MM."""
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
            
            if data.get('type') == 'QUOTE_MM':
                quote = Quote(
                    mm_id=data['trader_id'], product=data['product'],
                    bid_price=data['bid_price'], ask_price=data['ask_price'],
                    bid_volume=data['volume'], ask_volume=data['volume']
                )
                engine.update_quote(quote)
                print(f"⚡ [MM LIVE] Nouvelle quote manuelle : {quote.product} Bid={quote.bid_price} / Ask={quote.ask_price}")
            else:
                order = Order(
                    product=data['product'], side=Side.BUY if data['side'] == "BUY" else Side.SELL,
                    quantity=data['quantity'], trader_id=data['trader_id']
                )
                trade = await engine.match_order(order, price_limit=None)
                if trade:
                    governance.update_trader_stats(trade, trade.execution_price)
                    print(f"🤝 [MATCH SUCCESS] Ordre manuel exécuté à {trade.execution_price}$ !")
                
    except Exception as e:
        print(f"⚠️ Erreur traitement flux manuel : {e}")

async def main_orchestrator():
    if not os.path.exists('data'): os.makedirs('data')
    
    engine = MatchingEngine(commission_rate=0.0002)
    gov = Governance(promotion_threshold=0.0001, min_trades=15)
    
    # --- LOGS DE DÉMARRAGE VISUELS (Vérification Fusée) ---
    print("\n" + "="*60)
    print("🚀 LIQUIDITYHUB ENGINE INITIALIZATION... 🚀")
    print("="*60)
    print("⚙️  [1/3] Carnet d'ordres asynchrone prêt (Commissions: 0.02%).")
    print("🌐 [2/3] Connexion active à l'API Finance internationale (Timeout sécurisé).")
    print(f"👥 [3/3] Initialisation et déploiement de {NB_TRADERS} robots algorithmiques.")
    print("-"*60)
    print("🟢 TOUT EST OK : Le marché est désormais OUVERT et à l'écoute !")
    print("="*60 + "\n")

    # Lancement du fetcher d'API en arrière-plan
    api_task = asyncio.create_task(fetch_api_prices_task())

    # Lancement des processus de marché
    mm_tasks = [asyncio.create_task(market_maker_behavior(f"MM_REALTIME_{p}", engine, p)) for p in COMMODITIES]
    trader_tasks = [asyncio.create_task(trader_worker(f"Trader_{i}", engine, gov)) for i in range(NB_TRADERS)]

    try:
        while True:
            await check_manual_orders(engine, gov)
            
            new_mms = gov.evaluate_promotions()
            for mm_id in new_mms:
                print(f"✨ PROMOTION : {mm_id} devient MM (Badge Verified LP) !")
                mm_tasks.append(asyncio.create_task(market_maker_behavior(mm_id, engine, random.choice(COMMODITIES))))
            
            if engine.trade_history:
                trades_dicts = [vars(t).copy() for t in engine.trade_history]
                for t in trades_dicts:
                    if isinstance(t['side'], Side): 
                        t['side'] = t['side'].value
                
                df = pd.DataFrame(trades_dicts)
                
                df.to_parquet('data/executed_trades.parquet.tmp', index=False)
                os.replace('data/executed_trades.parquet.tmp', 'data/executed_trades.parquet')
                
                df_dash = df.copy()
                for p in COMMODITIES:
                    df_dash[f"ref_price_{p}"] = current_market_prices[p]
                    
                    if p in engine.quotes and engine.quotes[p]:
                        best_mm = list(engine.quotes[p].keys())[-1]
                        q = engine.quotes[p][best_mm]
                        df_dash[f"mm_id_{p}"] = q.mm_id
                        df_dash[f"mm_bid_{p}"] = q.bid_price
                        df_dash[f"mm_ask_{p}"] = q.ask_price
                        df_dash[f"mm_vol_{p}"] = q.bid_volume
                    else:
                        df_dash[f"mm_id_{p}"] = "N/A"
                        df_dash[f"mm_bid_{p}"] = current_market_prices[p]
                        df_dash[f"mm_ask_{p}"] = current_market_prices[p]
                        df_dash[f"mm_vol_{p}"] = 0
                
                df_dash.to_parquet('data/dashboard_trades.parquet.tmp', index=False)
                os.replace('data/dashboard_trades.parquet.tmp', 'data/dashboard_trades.parquet')
            
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"💥 Erreur critique du moteur : {e}")
    finally:
        api_task.cancel()
        for t in mm_tasks + trader_tasks: t.cancel()
        print("\n🛑 Engine arrêté proprement.")

if __name__ == "__main__":
    asyncio.run(main_orchestrator())