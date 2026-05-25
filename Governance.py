import numpy as np
from typing import Dict, List
from MarketTypes import Trade, TraderProfile, Role, Side

class Governance:
    def __init__(self, target_alpha: float = 0.0001, min_trades: int = 15, max_drawdown_pct: float = 0.05):
        self.profiles: Dict[str, TraderProfile] = {}
        self.target_alpha = target_alpha        # Alpha minimum requis (ex: 1 point de base)
        self.min_trades = min_trades            # Nombre minimum d'exécutions pour valider le test
        self.max_drawdown_pct = max_drawdown_pct  # 5% de perte max autorisée sous peine d'élimination
        self.initial_balance = 100000.0         # Balance théorique de départ du compte d'évaluation

    def update_trader_stats(self, trade: Trade, current_market_mid: float):
        """Analyse en temps réel la performance et le risque du candidat au challenge."""
        t_id = trade.trader_id
        if t_id not in self.profiles:
            self.profiles[t_id] = TraderProfile(trader_id=t_id)
        
        prof = self.profiles[t_id]
        prof.total_volume += trade.quantity
        
        # 1. Calcul du PnL simulé du trade pour le suivi du Drawdown
        trade_value = trade.execution_price * trade.quantity
        if trade.side == Side.BUY:
            # Si le trader achète, une hausse du mid génère du PnL
            pnl_impact = (current_market_mid - trade.execution_price) * trade.quantity
        else:
            # Si le trader vend, une baisse du mid génère du PnL
            pnl_impact = (trade.execution_price - current_market_mid) * trade.quantity
            
        prof.realized_pnl += pnl_impact - trade.commission

        # 2. Calcul de l'Edge (Sélection Adverse / Alpha)
        # Mesure si le trader entre au bon moment avant un mouvement de prix
        if trade.side == Side.BUY:
            edge = (current_market_mid - trade.execution_price) / trade.execution_price
        else:
            edge = (trade.execution_price - current_market_mid) / current_market_mid
        
        prof.edge_history.append(edge)
        
        # Fenêtre glissante sur les 100 derniers trades pour l'Alpha glissant
        if len(prof.edge_history) > 100:
            prof.edge_history.pop(0)
        prof.alpha_score = np.mean(prof.edge_history)

        # 3. Surveillance du Risque (Drawdown)
        current_balance = self.initial_balance + prof.realized_pnl
        loss_pct = (self.initial_balance - current_balance) / self.initial_balance
        
        if loss_pct > self.max_drawdown_pct:
            if prof.role != Role.CHALLENGE_CANDIDATE:
                print(f"🚨 ALERTE RISK MANAGEMENT : Trader Financé {t_id} a violé la règle de Drawdown ({loss_pct:.2%}).")
            prof.is_verified = False
            prof.allocated_capital = 0.0

    def evaluate_promotions(self) -> List[str]:
        """Analyse la base colonnaire pour identifier les candidats ayant réussi le challenge."""
        promoted_ids = []
        for t_id, prof in self.profiles.items():
            # Critères de réussite : Rôle de candidat, volume de trades suffisant, Alpha positif, et PnL positif
            if prof.role == Role.CHALLENGE_CANDIDATE and len(prof.edge_history) >= self.min_trades:
                if prof.alpha_score > self.target_alpha and prof.realized_pnl > 0:
                    prof.role = Role.FUNDED_TRADER
                    prof.is_verified = True
                    prof.allocated_capital = 500000.0  # Allocation d'un demi-million de capital réel/répliqué
                    promoted_ids.append(t_id)
        return promoted_ids

    def get_funded_leaderboard(self):
        """Prépare les statistiques d'Alpha pour les investisseurs et le dashboard d'administration."""
        leaderboard = []
        for t_id, prof in self.profiles.items():
            if prof.role == Role.FUNDED_TRADER and prof.is_verified:
                leaderboard.append({
                    "id_anonyme": f"FT-{t_id[:6]}",
                    "alpha_score": round(prof.alpha_score * 10000, 2), # Exprimé en points de base (bps)
                    "pnl_cumule": round(prof.realized_pnl, 2),
                    "capital_alloue": prof.allocated_capital,
                    "statut": "Actif (Verified)"
                })
        return sorted(leaderboard, key=lambda x: x['alpha_score'], reverse=True)