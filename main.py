import asyncio
import random
import time
import pandas as pd
from datetime import datetime

# Configuration
COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F']
NB_MONKEYS = 10
ORDERS_PER_MONKEY = 1000

async def monkey_trader_worker(trader_id, queue, nb_orders):
    """
    Etape 1 : Producteur d'ordres asynchrone
    """
    for _ in range(nb_orders):
        order = {
            "order_id": f"ord_{trader_id}_{random.getrandbits(32)}",
            "timestamp": datetime.now().isoformat(),
            "trader_id": f"trader_{trader_id}",
            "trader_type": "MONKEY",
            "product": random.choice(COMMODITIES),
            "quantity": random.randint(1, 50),
            "side": random.choice(["BUY", "SELL"]),
            "price_target": round(random.uniform(10, 2000), 2)
        }
        await queue.put(order)
        await asyncio.sleep(random.uniform(0.0001, 0.001))

async def ingestion_worker(queue, trades_storage):
    """
    Etape 2 : Ingestion et gestion de la file d'attente
    Consomme les ordres de la queue pour eviter l'accumulation en memoire.
    """
    orders_processed = 0
    total_expected = NB_MONKEYS * ORDERS_PER_MONKEY
    
    while orders_processed < total_expected:
        # Recuperation de l'ordre dans la file
        order = await queue.get()
        
        # Stockage temporaire avant ecriture disque (Etape 3)
        trades_storage.append(order)
        
        orders_processed += 1
        
        # On informe la queue que la tache est traitee
        queue.task_done()
        
        if orders_processed % 1000 == 0:
            print(f"Ingestion : {orders_processed} ordres recuperes dans la file...")

async def main_simulation():
    # Initialisation de la Queue (le tampon anti-Data Race)
    order_queue = asyncio.Queue()
    
    # Liste de stockage en memoire vive
    trades_storage = []
    
    print(f"Demarrage du systeme : {NB_MONKEYS * ORDERS_PER_MONKEY} ordres attendus")
    start_time = time.perf_counter()

    # Lancement du consommateur (Etape 2)
    consumer = asyncio.create_task(ingestion_worker(order_queue, trades_storage))

    # Lancement des producteurs (Etape 1)
    producers = [
        asyncio.create_task(monkey_trader_worker(i, order_queue, ORDERS_PER_MONKEY))
        for i in range(NB_MONKEYS)
    ]

    # On attend que les producteurs terminent
    await asyncio.gather(*producers)
    
    # On attend que le consommateur ait fini de vider la queue
    await consumer
    
    # Etape de persistance Big Data
    print("Sauvegarde des donnees au format Parquet...")
    df = pd.DataFrame(trades_storage)
    df.to_parquet('data/raw_trades.parquet', engine='pyarrow')
    
    end_time = time.perf_counter()
    print(f"Systeme arrete. Total traite : {len(df)} ordres.")
    print(f"Temps total : {end_time - start_time:.2f} secondes.")

if __name__ == "__main__":
    asyncio.run(main_simulation())