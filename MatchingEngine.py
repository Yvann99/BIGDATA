import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from MarketTypes import Order, Trade, Quote, Side, Role

class MatchingEngine:
    def __init__(self, commission_rate: float = 0.0001):
        # Carnet d'ordres : { "PRODUCT": { "MM_ID": Quote } }
        self.quotes: Dict[str, Dict[str, Quote]] = {}
        self.commission_rate = commission_rate # 0.01% par défaut
        self.trade_history: List[Trade] = []

    def update_quote(self, quote: Quote):
        """Met à jour ou ajoute une proposition de prix d'un Market Maker."""
        if quote.product not in self.quotes:
            self.quotes[quote.product] = {}
        self.quotes[quote.product][quote.mm_id] = quote

    def get_best_quote(self, product: str, side: Side) -> Optional[Quote]:
        """Trouve la meilleure offre anonyme (Best Bid / Best Offer)."""
        product_quotes = self.quotes.get(product, {})
        if not product_quotes:
            return None

        if side == Side.BUY:
            # Le client veut acheter -> On cherche le prix de vente (ASK) le plus bas des MM
            return min(product_quotes.values(), key=lambda q: q.ask_price)
        else:
            # Le client veut vendre -> On cherche le prix d'achat (BID) le plus haut des MM
            return max(product_quotes.values(), key=lambda q: q.bid_price)

    async def match_order(self, order: Order) -> Optional[Trade]:
        """Tente de faire correspondre un ordre client avec la meilleure quote MM."""
        best_q = self.get_best_quote(order.product, order.side)
        
        if not best_q:
            return None

        # Vérification sommaire de la liquidité (volume)
        if order.side == Side.BUY and best_q.ask_volume < order.quantity:
            return None # Pas assez de stock chez ce MM
        elif order.side == Side.SELL and best_q.bid_volume < order.quantity:
            return None

        # Détermination du prix d'exécution
        exec_price = best_q.ask_price if order.side == Side.BUY else best_q.bid_price
        
        # Calcul de la commission de la plateforme
        notional = exec_price * order.quantity
        commission = notional * self.commission_rate

        # Création du Trade
        trade = Trade(
            trade_id=f"TRD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{order.trader_id[:4]}",
            order_id=order.order_id,
            product=order.product,
            side=order.side,
            quantity=order.quantity,
            execution_price=round(exec_price, 5),
            mm_id=best_q.mm_id, # L'ID est connu du moteur mais sera masqué sur le dashboard
            trader_id=order.trader_id,
            commission=round(commission, 5)
        )

        self.trade_history.append(trade)
        
        # Mise à jour fictive du volume restant chez le MM (pour la simulation)
        if order.side == Side.BUY:
            best_q.ask_volume -= order.quantity
        else:
            best_q.bid_volume -= order.quantity

        return trade

    def get_market_snapshot(self, product: str):
        """Retourne les meilleurs prix anonymisés pour le Dashboard."""
        best_ask = self.get_best_quote(product, Side.BUY)
        best_bid = self.get_best_quote(product, Side.SELL)
        
        return {
            "product": product,
            "best_bid": best_bid.bid_price if best_bid else None,
            "best_ask": best_ask.ask_price if best_ask else None,
            "spread": (best_ask.ask_price - best_bid.bid_price) if best_ask and best_bid else None
        }