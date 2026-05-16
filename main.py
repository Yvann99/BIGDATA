import asyncio
import random
import pandas as pd
import os
import json
from datetime import datetime

# Import de tes modules locaux
from MarketTypes import Order, Trade, Quote, Side, Role, TraderProfile
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
    """Simule un client automatique envoyant des ordres."""
    for _ in range(ORDERS_PER_TRADER):
        product = random.choice(COMMODITIES)
        side = random.choice([Side.BUY, Side.SELL])
        order = Order(product=product, side=side, quantity=random.randint(1, 10), trader_id=trader_id)
        
        trade = await engine.match_order(order)
        if trade:
            future_mid = trade.execution_price * random.uniform(0.999, 1.001)
            governance.update_trader_stats(trade, future_mid)
        await asyncio.sleep(random.uniform(0.1, 0.5))

async def check_manual_orders(engine, governance):
    """Consomme les ordres du Terminal Trader (Dashboard) avec traçage ligne par ligne."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, 'data', 'pending_orders.json')
    
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return

    print(f"🔥 Fichier trouvé ! Taille : {os.path.getsize(path)} octets. Tentative de lecture...")

    try:
        # 1. Lecture complète des lignes
        with open(path, 'r') as f:
            lines = f.readlines()
        
        # 2. Vidage immédiat du fichier sur le disque pour libérer VS Code et le Dashboard
        with open(path, 'w') as f:
            f.truncate()
        print(f"📥 {len(lines)} ligne(s) récupérée(s). File d'attente vidée sur le disque.")
            
        for i, line in enumerate(lines):
            if not line.strip(): 
                continue
            
            print(f"🧩 Analyse de la ligne {i+1}...")
            data = json.loads(line)
            
            order = Order(
                product=data['product'],
                side=Side.BUY if data['side'] == "BUY" else Side.SELL,
                quantity=data['quantity'],
                trader_id=data['trader_id']
            )
            
            print(f"⚡ Envoi de l'ordre {order.side.value} au MatchingEngine...")
            
            # Vérification de sécurité pour le await
            if asyncio.iscoroutinefunction(engine.match_order):
                trade = await engine.match_order(order, price_limit=None)
            else:
                trade = engine.match_order(order, price_limit=None)
                
            print("⚙️ Retour du MatchingEngine obtenu.")
            
            if trade:
                if order.trader_id not in governance.traders:
                    governance.traders[order.trader_id] = TraderProfile(trader_id=order.trader_id, role=Role.TRADER)
                governance.update_trader_stats(trade, trade.execution_price)
                print(f"🤝 [MATCH SUCCESS] Ordre exécuté à {trade.execution_price}$ ! Vos compteurs vont augmenter.")
            else:
                print("❌ [MATCH FAILED] Le moteur n'a pas pu matcher l'ordre.")
                
    except Exception as e:
        print(f"💥 CRASH DANS LA LECTURE : {e}")

async def main_orchestrator():
    if not os.path.exists('data'): os.makedirs('data')
    
    engine = MatchingEngine(commission_rate=0.0002)
    gov = Governance(promotion_threshold=0.0001, min_trades=15)
    
    print("🚀 LiquidityHub Engine Running...")

    # Lancement des MMs de base (Amorçage de la liquidité)
    mm_tasks = [asyncio.create_task(market_maker_behavior(f"MM_ORIGINAL_{p}", engine, p)) for p in COMMODITIES]
    # Lancement des clients simulés
    trader_tasks = [asyncio.create_task(trader_worker(f"Trader_{i}", engine, gov)) for i in range(NB_TRADERS)]

    try:
        # Boucle infinie pour maintenir le moteur actif indéfiniment pour la démo
        while True:
            # 1. Vérification et consommation immédiate du flux d'ordres manuels du Dashboard
            await check_manual_orders(engine, gov)
            
            # 2. Gestion des promotions via l'Alpha Score
            new_mms = gov.evaluate_promotions()
            for mm_id in new_mms:
                print(f"✨ PROMOTION : {mm_id} devient MM (Badge Verified LP) !")
                mm_tasks.append(asyncio.create_task(market_maker_behavior(mm_id, engine, random.choice(COMMODITIES))))
            
            # 3. SAUVEGARDE ATOMIQUE (Format Parquet pour le Dashboard)
            if engine.trade_history:
                trades_dicts = [vars(t).copy() for t in engine.trade_history]
                for t in trades_dicts:
                    if isinstance(t['side'], Side): t['side'] = t['side'].value
                
                df = pd.DataFrame(trades_dicts)
                # Utilisation du fichier temporaire pour éviter les conflits de lecture concurrents
                df.to_parquet('data/executed_trades.parquet.tmp', index=False)
                os.replace('data/executed_trades.parquet.tmp', 'data/executed_trades.parquet')
            
            # Fréquence d'interrogation haute performance (10 fois par seconde)
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"Erreur Moteur : {e}")
    finally:
        for t in mm_tasks: t.cancel()
        print("🛑 Engine arrêté proprement.")

if __name__ == "__main__":
    asyncio.run(main_orchestrator())