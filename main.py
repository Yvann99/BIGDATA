import asyncio
import random
import pandas as pd
import os
import json
import yfinance as yf

COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']
NB_TRADERS = 15

# Dictionnaire global pour stocker les derniers prix de l'API en mémoire
current_market_prices = {'CL=F': 105.0, 'GC=F': 2350.0, 'NG=F': 2.50, 'HG=F': 4.50, 'ZC=F': 4.60}

from MarketTypes import Order, Trade, Quote, Side, Role, TraderProfile
from MatchingEngine import MatchingEngine
from Governance import Governance

def update_real_market_prices():
    """Va chercher les vrais prix sur Yahoo Finance et met à jour la mémoire du moteur."""
    global current_market_prices
    for p in COMMODITIES:
        try:
            ticker = yf.Ticker(p)
            price = ticker.fast_info['last_price']
            if price and price > 0:
                current_market_prices[p] = round(float(price), 3)
        except Exception:
            pass # Conserve la valeur précédente ou le fallback en cas d'échec

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
            
        await asyncio.sleep(random.uniform(0.5, 1.5))

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
            
            # DISTINCTION : Est-ce une Quote manuelle du MM ou un Ordre classique ?
            if data.get('type') == 'QUOTE_MM':
                quote = Quote(
                    mm_id=data['trader_id'], product=data['product'],
                    bid_price=data['bid_price'], ask_price=data['ask_price'],
                    bid_volume=data['volume'], ask_volume=data['volume']
                )
                engine.update_quote(quote)
                print(f"⚡ [MM LIVE] Nouvelles quotes injectées pour {quote.product} : Bid={quote.bid_price} / Ask={quote.ask_price}")
            else:
                # Ordre classique
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
    
    print("🚀 LiquidityHub Engine Running with Real-Time Finance API...")

    mm_tasks = [asyncio.create_task(market_maker_behavior(f"MM_REALTIME_{p}", engine, p)) for p in COMMODITIES]
    trader_tasks = [asyncio.create_task(trader_worker(f"Trader_{i}", engine, gov)) for i in range(NB_TRADERS)]

    try:
        while True:
            # 1. Mise à jour des cours réels
            update_real_market_prices()
            
            # 2. Lecture des ordres/quotes du Dashboard
            await check_manual_orders(engine, gov)
            
            # 3. Promotions
            new_mms = gov.evaluate_promotions()
            for mm_id in new_mms:
                mm_tasks.append(asyncio.create_task(market_maker_behavior(mm_id, engine, random.choice(COMMODITIES))))
            
            # 4. Sauvegarde Parquet enrichie (Correction pour ne pas bloquer la Gouvernance)
            if engine.trade_history:
                # On crée une copie superficielle pour le Dashboard pour ne pas polluer la mémoire du moteur
                trades_dicts = [vars(t).copy() for t in engine.trade_history]
                for t in trades_dicts:
                    if isinstance(t['side'], Side): 
                        t['side'] = t['side'].value
                
                df = pd.DataFrame(trades_dicts)
                
                # Sauvegarde brute pour la Gouvernance (si elle lit le Parquet en interne)
                df.to_parquet('data/executed_trades.parquet.tmp', index=False)
                os.replace('data/executed_trades.parquet.tmp', 'data/executed_trades.parquet')
                
                # Sauvegarde enrichie SPECIFIQUE pour le Dashboard (avec un autre nom pour isoler les prix d'API)
                df_dash = df.copy()
                for p in COMMODITIES:
                    df_dash[f"ref_price_{p}"] = current_market_prices[p]
                
                df_dash.to_parquet('data/dashboard_trades.parquet.tmp', index=False)
                os.replace('data/dashboard_trades.parquet.tmp', 'data/dashboard_trades.parquet')
            
    except Exception as e:
        print(f"Erreur Moteur : {e}")
    finally:
        for t in mm_tasks + trader_tasks: t.cancel()

if __name__ == "__main__":
    asyncio.run(main_orchestrator())