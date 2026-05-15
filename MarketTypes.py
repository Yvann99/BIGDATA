from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
import uuid

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class Role(Enum):
    TRADER = "TRADER"         # Client classique (Monkey ou autre)
    MARKET_MAKER = "MARKET_MAKER"  # Trader promu fournissant de la liquidité

@dataclass
class Order:
    """Représente un ordre envoyé par un client vers la plateforme."""
    product: str
    side: Side
    quantity: int
    trader_id: str
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    price_target: Optional[float] = None  # Pour un ordre Limit (optionnel ici)

@dataclass
class Trade:
    """Représente une exécution confirmée entre un client et un Market Maker."""
    trade_id: str
    order_id: str
    product: str
    side: Side  # Du point de vue du client
    quantity: int
    execution_price: float
    mm_id: str  # ID du Market Maker qui a fourni la liquidité (Anonymisé sur le dashboard)
    trader_id: str
    commission: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Quote:
    """Prix proposé par un Market Maker pour être affiché dans le carnet d'ordres."""
    mm_id: str
    product: str
    bid_price: float  # Prix auquel le MM achète
    ask_price: float  # Prix auquel le MM vend
    bid_volume: int
    ask_volume: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TraderProfile:
    """Suivi de la performance pour la gouvernance et la promotion."""
    trader_id: str
    role: Role = Role.TRADER
    total_volume: int = 0
    realized_pnl: float = 0.0
    # Score d'Alpha : mesure la capacité à anticiper le marché
    alpha_score: float = 0.0 
    # Historique des prix post-trade pour évaluer la qualité du trader
    edge_history: List[float] = field(default_factory=list)
    allocated_liquidity: float = 0.0  # Capital prêté par la plateforme si promu MM