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
    """Consomme les ordres du Terminal Trader (Dashboard) et force l'exécution au marché."""
    path = 'data/pending_orders.json'
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return
    print("Vérification du fichier JSON...")
    try:
        # 1. Lecture et vidage immédiat de la file d'attente pour éviter les doublons
        with open(path, 'r+') as f:
            lines = f.readlines()
            f.seek(0)
            f.truncate()
            
        for line in lines:
            if not line.strip(): 
                continue
            data = json.loads(line)
            
            # 2. Reconstruction de l'ordre client manuel
            order = Order(
                product=data['product'],
                side=Side.BUY if data['side'] == "BUY" else Side.SELL,
                quantity=data['quantity'],
                trader_id=data['trader_id']
            )
            
            print(f"📥 [LIVE] Traitement ordre client : {order.side.value} {order.quantity} {order.product}")
            
            # 3. FORCE LE MATCH AU MARCHÉ (price_limit=None) pour garantir l'exécution immédiate
            trade = await engine.match_order(order, price_limit=None)
            
            if trade:
                # Enregistrement du profil du trader manuel dans la gouvernance s'il n'existe pas
                if order.trader_id not in governance.traders:
                    governance.traders[order.trader_id] = TraderProfile(trader_id=order.trader_id, role=Role.TRADER)
                
                # Mise à jour des statistiques et du CA
                governance.update_trader_stats(trade, trade.execution_price)
                print(f"🤝 [MATCH SUCCESS] Ordre exécuté à {trade.execution_price}$ ! Compteurs mis à jour.")
            else:
                print(f"❌ [MATCH FAILED] Manque de volume disponible pour remplir l'ordre.")
                
    except Exception as e:
        print(f"⚠️ Erreur lors du traitement des ordres manuels : {e}")

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