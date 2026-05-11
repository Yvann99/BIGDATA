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
        # Le Trading Book : Position nette par produit
        self.inventory = {product: 0 for product in COMMODITIES}
        # Registre des trades executes
        self.executed_trades = []

    async def process_order(self, order):
        """
        Logique de l'Engine : Validation et Execution
        """
        # 1. Validation simple
        if order['quantity'] <= 0:
            return

        # 2. Execution (Market Making)
        # Si le client ACHETE, le Market Maker VEND (position diminue)
        # Si le client VEND, le Market Maker ACHETE (position augmente)
        qty = order['quantity']
        if order['side'] == 'BUY':
            self.inventory[order['product']] -= qty
        else:
            self.inventory[order['product']] += qty

        # 3. Enrichissement de la donnée (Ajout du prix d'execution)
        # Pour l'instant on utilise le target, l'algo de spread viendra a l'etape 4
        order['execution_price'] = order['price_target']
        order['status'] = 'EXECUTED'
        
        self.executed_trades.append(order)

async def monkey_trader_worker(trader_id, queue, nb_orders):
    for _ in range(nb_orders):
        order = {
            "order_id": f"ord_{trader_id}_{random.getrandbits(32)}",
            "timestamp": datetime.now().isoformat(),
            "trader_id": f"trader_{trader_id}",
            "product": random.choice(COMMODITIES),
            "quantity": random.randint(1, 50),
            "side": random.choice(["BUY", "SELL"]),
            "price_target": round(random.uniform(10, 2000), 2)
        }
        await queue.put(order)
        await asyncio.sleep(random.uniform(0.0001, 0.001))

async def engine_worker(queue, engine):
    """
    Etape 3 : La machine Engine consomme et valide les ordres
    """
    processed = 0
    total = NB_MONKEYS * ORDERS_PER_MONKEY
    
    while processed < total:
        order = await queue.get()
        
        # L'Engine traite l'ordre
        await engine.process_order(order)
        
        processed += 1
        queue.task_done()
        
        if processed % 1000 == 0:
            print(f"Engine : {processed} ordres executes dans le Trading Book")

async def main_simulation():
    if not os.path.exists('data'):
        os.makedirs('data')

    order_queue = asyncio.Queue()
    engine = TradingEngine()
    
    print(f"Demarrage de l'Engine : Traitement de {NB_MONKEYS * ORDERS_PER_MONKEY} trades...")
    start_time = time.perf_counter()

    # Lancement de l'Engine (Etape 3)
    engine_task = asyncio.create_task(engine_worker(order_queue, engine))

    # Lancement des Monkey Traders (Etape 1)
    producers = [
        asyncio.create_task(monkey_trader_worker(i, order_queue, ORDERS_PER_MONKEY))
        for i in range(NB_MONKEYS)
    ]

    await asyncio.gather(*producers)
    await engine_task
    
    # Sauvegarde finale du Trading Book execute
    df = pd.DataFrame(engine.executed_trades)
    df.to_parquet('data/executed_trades.parquet', engine='pyarrow')
    
    print("--- Rapport d'inventaire final du Market Maker ---")
    for prod, pos in engine.inventory.items():
        print(f"{prod} : {pos}")
    
    print(f"Simulation terminee en {time.perf_counter() - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(main_simulation())