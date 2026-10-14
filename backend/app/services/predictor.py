import numpy as np
from scipy.stats import poisson
from typing import Dict, List, Tuple
from collections import defaultdict
from app.models.schemas import Match, Prediction

class PoissonPredictor:
    """
    Bivariate Poisson model for football match prediction.
    
    For each team, estimates:
      - attack_strength: relative scoring ability
      - defense_weakness: relative conceding tendency
    Then computes goal expectations and outcome probabilities.
    """
    
    def __init__(self):
        self.team_attack: Dict[str, float] = {}
        self.team_defense: Dict[str, float] = {}
        self.league_home_advantage: float = 0.0
        self.league_avg_home_goals: float = 0.0
        self.league_avg_away_goals: float = 0.0
        self.is_fitted = False
    
    def fit(self, matches: List[Match]) -> None:
        """Fit model on historical matches with known scores."""
        home_goals = defaultdict(list)
        away_goals = defaultdict(list)
        
        total_home, total_away, n = 0, 0, 0
        
        for m in matches:
            if m.home_score is None or m.away_score is None:
                continue
            home_goals[m.home_team].append(m.home_score)
            away_goals[m.away_team].append(m.away_score)
            total_home += m.home_score
            total_away += m.away_score
            n += 1
        
        if n == 0:
            return
        
        self.league_avg_home_goals = total_home / n
        self.league_avg_away_goals = total_away / n
        
        # Attack strength = avg goals scored / league avg
        for team, goals in home_goals.items():
            home_avg = np.mean(goals)
            self.team_attack[team] = home_avg / max(self.league_avg_home_goals, 0.01)
        
        for team, goals in away_goals.items():
            away_avg = np.mean(goals)
            existing = self.team_attack.get(team, 1.0)
            # Blend home and away attack
            self.team_attack[team] = (existing + away_avg / max(self.league_avg_away_goals, 0.01)) / 2
        
        # Defense weakness = avg goals conceded / league avg
        for team in list(home_goals.keys()) + list(away_goals.keys()):
            conceded = []
            for m in matches:
                if m.home_score is None:
                    continue
                if m.home_team == team:
                    conceded.append(m.away_score)
                elif m.away_team == team:
                    conceded.append(m.home_score)
            if conceded:
                self.team_defense[team] = np.mean(conceded) / max(
                    (self.league_avg_home_goals + self.league_avg_away_goals) / 2, 0.01
                )
            else:
                self.team_defense[team] = 1.0
        
        # Home advantage
        self.league_home_advantage = self.league_avg_home_goals - self.league_avg_away_goals
        self.is_fitted = True
    
    def predict(self, home_team: str, away_team: str, match_id: str) -> Prediction:
        """Predict match outcome using fitted strengths."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        home_attack = self.team_attack.get(home_team, 1.0)
        away_attack = self.team_attack.get(away_team, 1.0)
        home_defense = self.team_defense.get(home_team, 1.0)
        away_defense = self.team_defense.get(away_team, 1.0)
        
        # Expected goals
        lambda_home = (self.league_avg_home_goals * home_attack * away_defense)
        lambda_away = (self.league_avg_away_goals * away_attack * home_defense)
        
        # Cap at reasonable max to avoid nonsense
        lambda_home = min(max(lambda_home, 0.1), 5.0)
        lambda_away = min(max(lambda_away, 0.1), 5.0)
        
        # Compute outcome probabilities via Poisson PMF (0-10 goals)
        max_goals = 10
        home_probs = [poisson.pmf(i, lambda_home) for i in range(max_goals)]
        away_probs = [poisson.pmf(i, lambda_away) for i in range(max_goals)]
        
        home_win = sum(home_probs[i] * sum(away_probs[:i]) for i in range(max_goals))
        draw = sum(home_probs[i] * away_probs[i] for i in range(max_goals))
        away_win = sum(away_probs[i] * sum(home_probs[:i]) for i in range(max_goals))
        
        total = home_win + draw + away_win
        home_win, draw, away_win = home_win/total, draw/total, away_win/total
        
        # Confidence based on how "decisive" the prediction is
        max_prob = max(home_win, draw, away_win)
        if max_prob > 0.55:
            confidence = "HIGH"
        elif max_prob > 0.42:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        return Prediction(
            match_id=match_id,
            home_win_prob=round(home_win, 4),
            draw_prob=round(draw, 4),
            away_win_prob=round(away_win, 4),
            predicted_home_goals=round(lambda_home, 2),
            predicted_away_goals=round(lambda_away, 2),
            model="Poisson",
            confidence=confidence,
        )


def find_value_bets(predictions: List[Prediction], 
                    matches: List[Match],
                    min_ev: float = 0.05) -> List[dict]:
    """
    Compare model probabilities against bookmaker odds.
    A value bet exists when model_prob > implied_prob + margin.
    """
    value_bets = []
    pred_map = {p.match_id: p for p in predictions}
    
    for match in matches:
        pred = pred_map.get(match.id)
        if not pred or not match.odds:
            continue
        
        for odds in match.odds:
            # Home
            if odds.home_win > 1.0:
                implied = 1.0 / odds.home_win
                ev = (pred.home_win_prob * odds.home_win) - 1
                if ev >= min_ev and pred.home_win_prob > implied:
                    value_bets.append({
                        "match_id": match.id,
                        "match_label": f"{match.home_team} vs {match.away_team}",
                        "selection": "HOME",
                        "bookmaker": odds.bookmaker,
                        "bookmaker_odds": odds.home_win,
                        "model_probability": pred.home_win_prob,
                        "implied_probability": round(implied, 4),
                        "expected_value": round(ev, 4),
                        "confidence": pred.confidence,
                    })
            
            # Draw
            if odds.draw > 1.0:
                implied = 1.0 / odds.draw
                ev = (pred.draw_prob * odds.draw) - 1
                if ev >= min_ev and pred.draw_prob > implied:
                    value_bets.append({
                        "match_id": match.id,
                        "match_label": f"{match.home_team} vs {match.away_team}",
                        "selection": "DRAW",
                        "bookmaker": odds.bookmaker,
                        "bookmaker_odds": odds.draw,
                        "model_probability": pred.draw_prob,
                        "implied_probability": round(implied, 4),
                        "expected_value": round(ev, 4),
                        "confidence": pred.confidence,
                    })
            
            # Away
            if odds.away_win > 1.0:
                implied = 1.0 / odds.away_win
                ev = (pred.away_win_prob * odds.away_win) - 1
                if ev >= min_ev and pred.away_win_prob > implied:
                    value_bets.append({
                        "match_id": match.id,
                        "match_label": f"{match.home_team} vs {match.away_team}",
                        "selection": "AWAY",
                        "bookmaker": odds.bookmaker,
                        "bookmaker_odds": odds.away_win,
                        "model_probability": pred.away_win_prob,
                        "implied_probability": round(implied, 4),
                        "expected_value": round(ev, 4),
                        "confidence": pred.confidence,
                    })
    
    return sorted(value_bets, key=lambda x: x["expected_value"], reverse=True)