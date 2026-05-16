import asyncio
import random
import pandas as pd
import os
import json
from datetime import datetime
import yfinance as yf

# Import de tes modules locaux
from MarketTypes import Order, Trade, Quote, Side, Role, TraderProfile
from MatchingEngine import MatchingEngine
from Governance import Governance

COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']
NB_TRADERS = 15

def get_real_market_price(product: str) -> float:
    """Récupère le dernier prix réel sur Yahoo Finance."""
    try:
        ticker = yf.Ticker(product)
        price = ticker.fast_info['last_price']
        if price and price > 0:
            return float(price)
    except Exception:
        pass
    
    # Prix de secours réalistes si le marché est fermé (Week-end) ou si l'API coupe
    fallback = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}
    return fallback.get(product, 100.0)

async def market_maker_behavior(mm_id, engine, product):
    """Simule un Market Maker calé sur les prix réels de l'API Finance."""
    while True:
        base_price = get_real_market_price(product)
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
            
        await asyncio.sleep(random.uniform(0.5, 1.5))

async def check_manual_orders(engine, governance):
    """Consomme les ordres du Terminal Trader (Dashboard) et force l'exécution au marché."""
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
                product=data['product'],
                side=Side.BUY if data['side'] == "BUY" else Side.SELL,
                quantity=data['quantity'],
                trader_id=data['trader_id']
            )
            
            trade = await engine.match_order(order, price_limit=None)
            
            if trade:
                # CORRECTION : On utilise directement la méthode update_trader_stats.
                # Si le trader n'existe pas dans la gouvernance, cette méthode l'initialise automatiquement
                # en interne, ce qui nous évite de manipuler directement l'attribut caché.
                governance.update_trader_stats(trade, trade.execution_price)
                print(f"🤝 [MATCH SUCCESS] Ordre manuel exécuté au prix réel de {trade.execution_price}$ !")
                
    except Exception as e:
        print(f"⚠️ Erreur lors du traitement des ordres manuels : {e}")
        
async def main_orchestrator():
    if not os.path.exists('data'): os.makedirs('data')
    
    engine = MatchingEngine(commission_rate=0.0002)
    gov = Governance(promotion_threshold=0.0001, min_trades=15)
    
    print("🚀 LiquidityHub Engine Running with Real-Time Finance API...")

    # Lancement des MMs connectés à l'API pour chaque commodité
    mm_tasks = [asyncio.create_task(market_maker_behavior(f"MM_REALTIME_{p}", engine, p)) for p in COMMODITIES]
    # Lancement des clients simulés à l'infini
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
                    if isinstance(t['side'], Side): t['side'] = t['side'].value
                
                df = pd.DataFrame(trades_dicts)
                df.to_parquet('data/executed_trades.parquet.tmp', index=False)
                os.replace('data/executed_trades.parquet.tmp', 'data/executed_trades.parquet')
            
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"Erreur Moteur : {e}")
    finally:
        for t in mm_tasks + trader_tasks: t.cancel()
        print("🛑 Engine arrêté proprement.")

if __name__ == "__main__":
    asyncio.run(main_orchestrator())