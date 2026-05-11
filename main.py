import asyncio
import random
import time
from datetime import datetime

# Liste des matieres premieres pour la simulation
COMMODITIES = ['CL=F', 'GC=F', 'NG=F', 'HG=F', 'ZC=F'] #Crude oil, Gold, Natural Gas, Copper, Corn

async def monkey_trader_worker(trader_id, queue, nb_orders): #Contrairement à une fonction classique, cette coroutine peut s'interrompre (pauser) pour laisser d'autres tâches s'exécuter
    """
    Simule un trader 'singe' qui envoie des ordres de maniere aleatoire.
    """
    for _ in range(nb_orders):
        # Generation d'un dictionnaire d'ordre
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
        
        # Injection dans la queue asynchrone (Etape 2)
        await queue.put(order)
        
        # Simulation d'une latence de haute frequence
        await asyncio.sleep(random.uniform(0.0001, 0.001))

async def main_simulation():
    # Initialisation de la Queue (Etape 2)
    order_queue = asyncio.Queue()
    
    nb_monkeys = 10
    orders_per_monkey = 1000  # Total 10 000 ordres
    
    print(f"Lancement de {nb_monkeys} Monkey Traders pour {nb_monkeys * orders_per_monkey} ordres...")
    start_time = time.perf_counter()

    # Creation des taches de production (Etape 1)
    producers = [
        asyncio.create_task(monkey_trader_worker(i, order_queue, orders_per_monkey))
        for i in range(nb_monkeys)
    ]

    # Attente de la fin de generation des ordres
    await asyncio.gather(*producers)
    
    end_time = time.perf_counter()
    print(f"Flux genere : {order_queue.qsize()} ordres dans la queue.")
    print(f"Temps ecoule : {end_time - start_time:.2f} secondes.")

if __name__ == "__main__":
    asyncio.run(main_simulation())