import asyncio
import random
import pandas as pd
import os
from datetime import datetime

# Import de tes modules locaux
from MarketTypes import Order, Trade, Quote, Side, Role
from MatchingEngine import MatchingEngine
from Governance import Governance

COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']
NB_TRADERS = 15
ORDERS_PER_TRADER = 100

async def market_maker_behavior(mm_id, engine, product):
    """Simule un Market Maker qui met à jour ses prix en continu."""
    while True:
        base_price = random.uniform(50, 1500)
        spread = base_price * 0.001
        quote = Quote(
            mm_id=mm_id, product=product,
            bid_price=round(base_price - (spread/2), 3),
            ask_price=round(base_price + (spread/2), 3),
            bid_volume=random.randint(100, 500),
            ask_volume=random.randint(100, 500)
        )
        engine.update_quote(quote)
        await asyncio.sleep(0.2)

async def trader_worker(trader_id, engine, governance):
    """Simule un client envoyant des ordres."""
    for _ in range(ORDERS_PER_TRADER):
        product = random.choice(COMMODITIES)
        side = random.choice([Side.BUY, Side.SELL])
        order = Order(product=product, side=side, quantity=random.randint(1, 10), trader_id=trader_id)
        
        trade = await engine.match_order(order)
        if trade:
            future_mid = trade.execution_price * random.uniform(0.999, 1.001)
            governance.update_trader_stats(trade, future_mid)
        await asyncio.sleep(random.uniform(0.1, 0.5))

async def main_orchestrator():
    if not os.path.exists('data'): os.makedirs('data')
    
    engine = MatchingEngine(commission_rate=0.0002)
    gov = Governance(promotion_threshold=0.0001, min_trades=15)
    
    print("🚀 LiquidityHub Engine Running...")

    # Lancement des MMs de base
    mm_tasks = [asyncio.create_task(market_maker_behavior(f"MM_ORIGINAL_{p}", engine, p)) for p in COMMODITIES]
    # Lancement des clients
    trader_tasks = [asyncio.create_task(trader_worker(f"Trader_{i}", engine, gov)) for i in range(NB_TRADERS)]

    try:
        while not all(t.done() for t in trader_tasks):
            # 1. Gestion des promotions
            new_mms = gov.evaluate_promotions()
            for mm_id in new_mms:
                print(f"✨ PROMOTION : {mm_id} devient MM !")
                mm_tasks.append(asyncio.create_task(market_maker_behavior(mm_id, engine, random.choice(COMMODITIES))))
            
            # 2. SAUVEGARDE ATOMIQUE (Live Experience)
            if engine.trade_history:
                trades_dicts = [vars(t).copy() for t in engine.trade_history]
                for t in trades_dicts:
                    if isinstance(t['side'], Side): t['side'] = t['side'].value
                
                df = pd.DataFrame(trades_dicts)
                # Écriture sécurisée : .tmp puis remplacement
                df.to_parquet('data/executed_trades.parquet.tmp', index=False)
                os.replace('data/executed_trades.parquet.tmp', 'data/executed_trades.parquet')
            
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        for t in mm_tasks: t.cancel()
        print("🛑 Engine arrêté proprement.")

if __name__ == "__main__":
    asyncio.run(main_orchestrator())