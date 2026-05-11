import asyncio
import random
import time
import pandas as pd
import os
from datetime import datetime

COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']
NB_MONKEYS = 10
ORDERS_PER_MONKEY = 1000

class TradingEngine:
    def __init__(self):
        self.inventory = {product: 0 for product in COMMODITIES}
        self.executed_trades = []
        # Simulation d'un prix de marche actuel
        self.market_prices = {product: random.uniform(50, 1500) for product in COMMODITIES}

    def calculate_dynamic_spread(self, product, side):
        """
        Etape 4 : Algorithme de spread dynamique
        """
        base_spread = 0.001  # 0.1% de marge de base
        
        # Ajustement selon l'inventaire (Gestion du risque)
        # Si on a trop vendu (short), on augmente le prix pour les acheteurs
        current_inv = self.inventory[product]
        inventory_risk_adjustment = 0
        
        if side == 'BUY' and current_inv < -500:
            inventory_risk_adjustment = 0.005 # +0.5% de marge pour freiner l'achat
        elif side == 'SELL' and current_inv > 500:
            inventory_risk_adjustment = 0.005 # +0.5% pour freiner la vente
            
        return base_spread + inventory_risk_adjustment

    async def process_order(self, order):
        if order['quantity'] <= 0:
            return

        product = order['product']
        side = order['side']
        mid_price = self.market_prices[product]
        
        # Calcul du spread dynamique
        spread_pct = self.calculate_dynamic_spread(product, side)
        
        # Calcul du prix d'execution final (Mid +/- Spread)
        if side == 'BUY':
            exec_price = mid_price * (1 + spread_pct)
            self.inventory[product] -= order['quantity']
        else:
            exec_price = mid_price * (1 - spread_pct)
            self.inventory[product] += order['quantity']

        order['execution_price'] = round(exec_price, 3)
        order['spread_applied'] = round(spread_pct, 5)
        order['status'] = 'EXECUTED'
        
        self.executed_trades.append(order)
        
        # Simulation legere de variation du prix de marche
        self.market_prices[product] *= random.uniform(0.999, 1.001)

async def monkey_trader_worker(trader_id, queue, nb_orders):
    for _ in range(nb_orders):
        order = {
            "order_id": f"ord_{trader_id}_{random.getrandbits(32)}",
            "timestamp": datetime.now().isoformat(),
            "trader_id": f"trader_{trader_id}",
            "product": random.choice(COMMODITIES),
            "quantity": random.randint(1, 50),
            "side": random.choice(["BUY", "SELL"]),
            "price_target": 0 # Sera ignore car l'engine fixe le prix maintenant
        }
        await queue.put(order)
        await asyncio.sleep(random.uniform(0.0001, 0.001))

async def engine_worker(queue, engine):
    processed = 0
    total = NB_MONKEYS * ORDERS_PER_MONKEY
    while processed < total:
        order = await queue.get()
        await engine.process_order(order)
        processed += 1
        queue.task_done()

async def main_simulation():
    if not os.path.exists('data'):
        os.makedirs('data')

    order_queue = asyncio.Queue()
    engine = TradingEngine()
    
    print("Demarrage du Trading Engine avec Spread Dynamique...")
    start_time = time.perf_counter()

    engine_task = asyncio.create_task(engine_worker(order_queue, engine))
    producers = [asyncio.create_task(monkey_trader_worker(i, order_queue, ORDERS_PER_MONKEY)) for i in range(NB_MONKEYS)]

    await asyncio.gather(*producers)
    await engine_task
    
    df = pd.DataFrame(engine.executed_trades)
    df.to_parquet('data/executed_trades.parquet', engine='pyarrow')
    
    print("\n--- Analyse du Trading Book ---")
    print(df[['product', 'side', 'execution_price', 'spread_applied']].head(10))
    
    print("\n--- Inventaire Final ---")
    for prod, pos in engine.inventory.items():
        print(f"{prod} : {pos}")
    
    print(f"\nSimulation terminee en {time.perf_counter() - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main_simulation())