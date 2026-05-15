import numpy as np
from typing import Dict, List
from MarketTypes import Trade, TraderProfile, Role, Side

class Governance:
    def __init__(self, promotion_threshold: float = 0.0005, min_trades: int = 50):
        self.profiles: Dict[str, TraderProfile] = {}
        self.promotion_threshold = promotion_threshold  # Edge moyen > 0.05%
        self.min_trades = min_trades
        self.market_dominance_limit = 0.70  # Un MM ne peut pas peser > 70% du volume

    def update_trader_stats(self, trade: Trade, current_market_mid: float):
        """Analyse la performance d'un trader après chaque exécution."""
        t_id = trade.trader_id
        if t_id not in self.profiles:
            self.profiles[t_id] = TraderProfile(trader_id=t_id)
        
        prof = self.profiles[t_id]
        prof.total_volume += trade.quantity
        
        # Calcul de l'Edge (Sélection Adverse)
        # Si le client achète et que le prix monte ensuite -> il est "informé"
        if trade.side == Side.BUY:
            edge = (current_market_mid - trade.execution_price) / trade.execution_price
        else:
            edge = (trade.execution_price - current_market_mid) / current_market_mid
        
        prof.edge_history.append(edge)
        
        # Mise à jour du score Alpha (moyenne mobile des derniers bords)
        if len(prof.edge_history) > 100:
            prof.edge_history.pop(0)
        prof.alpha_score = np.mean(prof.edge_history)

    def evaluate_promotions(self) -> List[str]:
        """Identifie les traders qui doivent devenir Market Makers."""
        promoted_ids = []
        for t_id, prof in self.profiles.items():
            if prof.role == Role.TRADER and len(prof.edge_history) >= self.min_trades:
                if prof.alpha_score > self.promotion_threshold:
                    prof.role = Role.MARKET_MAKER
                    prof.allocated_liquidity = 1000000.0  # Allocation initiale
                    promoted_ids.append(t_id)
        return promoted_ids

    def check_market_integrity(self, trades: List[Trade]) -> Dict[str, float]:
        """
        Calcule la dominance de chaque MM. 
        Si un MM devient 'le marché', il faut lever une alerte.
        """
        if not trades:
            return {}
            
        total_vol = sum(t.quantity for t in trades)
        mm_volumes = {}
        
        for t in trades:
            mm_volumes[t.mm_id] = mm_volumes.get(t.mm_id, 0) + t.quantity
            
        dominance = {mm: vol/total_vol for mm, vol in mm_volumes.items()}
        
        # Alertes de gouvernance
        for mm, share in dominance.items():
            if share > self.market_dominance_limit:
                print(f"⚠️ ALERTE GOUVERNANCE : Dominance excessive de {mm} ({share:.2%})")
                
        return dominance

    def get_mm_leaderboard(self):
        """Prépare les données pour le Dashboard anonyme."""
        leaderboard = []
        for t_id, prof in self.profiles.items():
            if prof.role == Role.MARKET_MAKER:
                leaderboard.append({
                    "id_anonyme": f"LP-{t_id[:6]}",
                    "alpha_score": round(prof.alpha_score * 10000, 2), # En points de base
                    "volume_total": prof.total_volume,
                    "statut": "Actif"
                })
        return sorted(leaderboard, key=lambda x: x['alpha_score'], reverse=True)