from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
import uuid

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class Role(Enum):
    CHALLENGE_CANDIDATE = "CHALLENGE_CANDIDATE"  # Trader en phase de test / évaluation
    FUNDED_TRADER = "FUNDED_TRADER"              # Trader d'élite validé et financé par la Prop Firm

@dataclass
class Order:
    """Représente un ordre envoyé par un candidat ou un trader financé."""
    product: str
    side: Side
    quantity: int
    trader_id: str
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    price_target: Optional[float] = None

@dataclass
class Trade:
    """Représente une exécution simulée dans l'environnement de la Prop Firm."""
    trade_id: str
    order_id: str
    product: str
    side: Side  
    quantity: int
    execution_price: float
    mm_id: str  # Reste l'ID du fournisseur de liquidité en arrière-plan (ex: le bot de la plateforme)
    trader_id: str
    commission: float  # Frais de courtage simulés appliqués par la Prop Firm
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Quote:
    """Prix proposé par le moteur de la plateforme (Liquidité de secours / BFI)."""
    mm_id: str
    product: str
    bid_price: float  
    ask_price: float  
    bid_volume: int
    ask_volume: int
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TraderProfile:
    """Suivi analytique Big Data de la performance pour l'évaluation et l'allocation de capital."""
    trader_id: str
    role: Role = Role.CHALLENGE_CANDIDATE
    total_volume: int = 0
    realized_pnl: float = 0.0
    
    # Score d'Alpha : mesure la capacité à surperformer le marché (flux non-toxique)
    alpha_score: float = 0.0
    edge_history: List[float] = field(default_factory=list)
    
    # Métriques spécifiques Prop Firm
    allocated_capital: float = 0.0  # Capital alloué après réussite du challenge
    is_verified: bool = False