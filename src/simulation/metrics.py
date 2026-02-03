"""
Metrics collection module for Monte Carlo simulations.

This module provides functions to calculate key metrics from simulation results:
- Win rate
- Median turn count
- Variance
- 5% tail-risk (catastrophic failure rate)
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import statistics


class SimulationMetrics:
    """
    Metrics calculator for Monte Carlo simulation results.
    
    Provides methods to calculate and analyze simulation outcomes.
    """
    
    def __init__(self, results: List[Dict[str, Any]]):
        """
        Initialize metrics calculator with simulation results.
        
        Args:
            results: List of simulation run results
        """
        self.results = results
        self._extract_data()
    
    def _extract_data(self):
        """Extract key data from results."""
        self.wins = [r.get("won", False) for r in self.results]
        self.turns = [r.get("turns_taken", 0) for r in self.results]
        self.final_hp = [r.get("player_hp", 0) for r in self.results]
        self.damage_dealt = [r.get("total_damage_dealt", 0) for r in self.results]
    
    def calculate_win_rate(self) -> float:
        """
        Calculate win rate as percentage.
        
        Returns:
            Win rate (0-100)
        """
        if not self.wins:
            return 0.0
        
        return (sum(self.wins) / len(self.wins)) * 100
    
    def calculate_median_turns(self) -> float:
        """
        Calculate median turn count.
        
        Returns:
            Median number of turns
        """
        if not self.turns:
            return 0.0
        
        return statistics.median(self.turns)
    
    def calculate_mean_turns(self) -> float:
        """
        Calculate mean turn count.
        
        Returns:
            Mean number of turns
        """
        if not self.turns:
            return 0.0
        
        return statistics.mean(self.turns)
    
    def calculate_variance(self) -> float:
        """
        Calculate variance in turn count.
        
        Returns:
            Variance of turn count
        """
        if len(self.turns) < 2:
            return 0.0
        
        return statistics.variance(self.turns)
    
    def calculate_std_deviation(self) -> float:
        """
        Calculate standard deviation in turn count.
        
        Returns:
            Standard deviation of turn count
        """
        if len(self.turns) < 2:
            return 0.0
        
        return statistics.stdev(self.turns)
    
    def calculate_tail_risk(self, percentile: float = 5.0) -> Dict[str, Any]:
        """
        Calculate tail-risk (catastrophic failure rate).
        
        The 5% tail-risk represents the worst 5% of outcomes.
        
        Args:
            percentile: Percentile for tail analysis (default: 5.0 for bottom 5%)
            
        Returns:
            Dictionary with tail-risk metrics
        """
        if not self.results:
            return {
                "percentile": percentile,
                "threshold_turns": 0,
                "failure_rate_in_tail": 0.0,
                "mean_hp_in_tail": 0.0,
                "count_in_tail": 0,
            }
        
        # Calculate threshold for bottom percentile
        threshold_turns = np.percentile(self.turns, percentile)
        
        # Get results in the tail (worst performing)
        tail_indices = [i for i, t in enumerate(self.turns) if t >= threshold_turns]
        
        if not tail_indices:
            return {
                "percentile": percentile,
                "threshold_turns": threshold_turns,
                "failure_rate_in_tail": 0.0,
                "mean_hp_in_tail": 0.0,
                "count_in_tail": 0,
            }
        
        # Calculate metrics for tail
        tail_wins = [self.wins[i] for i in tail_indices]
        tail_hp = [self.final_hp[i] for i in tail_indices]
        
        failure_rate = (1 - sum(tail_wins) / len(tail_wins)) * 100 if tail_wins else 0.0
        mean_hp = statistics.mean(tail_hp) if tail_hp else 0.0
        
        return {
            "percentile": percentile,
            "threshold_turns": float(threshold_turns),
            "failure_rate_in_tail": round(failure_rate, 2),
            "mean_hp_in_tail": round(mean_hp, 1),
            "count_in_tail": len(tail_indices),
        }
    
    def calculate_success_tail(self, percentile: float = 95.0) -> Dict[str, Any]:
        """
        Calculate success tail (best outcomes).
        
        Args:
            percentile: Percentile for success analysis (default: 95.0 for top 5%)
            
        Returns:
            Dictionary with success tail metrics
        """
        if not self.results:
            return {
                "percentile": percentile,
                "threshold_turns": 0,
                "win_rate_in_tail": 0.0,
                "mean_hp_in_tail": 0.0,
                "count_in_tail": 0,
            }
        
        # Calculate threshold for top percentile (fewer turns is better for wins)
        threshold_turns = np.percentile(self.turns, 100 - percentile)
        
        # Get results in the success tail (best performing)
        tail_indices = [i for i, t in enumerate(self.turns) if t <= threshold_turns]
        
        if not tail_indices:
            return {
                "percentile": percentile,
                "threshold_turns": threshold_turns,
                "win_rate_in_tail": 0.0,
                "mean_hp_in_tail": 0.0,
                "count_in_tail": 0,
            }
        
        # Calculate metrics for success tail
        tail_wins = [self.wins[i] for i in tail_indices]
        tail_hp = [self.final_hp[i] for i in tail_indices]
        
        win_rate = (sum(tail_wins) / len(tail_wins)) * 100 if tail_wins else 0.0
        mean_hp = statistics.mean(tail_hp) if tail_hp else 0.0
        
        return {
            "percentile": percentile,
            "threshold_turns": float(threshold_turns),
            "win_rate_in_tail": round(win_rate, 2),
            "mean_hp_in_tail": round(mean_hp, 1),
            "count_in_tail": len(tail_indices),
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all standard metrics.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            "win_rate": round(self.calculate_win_rate(), 2),
            "median_turns": round(self.calculate_median_turns(), 1),
            "mean_turns": round(self.calculate_mean_turns(), 1),
            "variance": round(self.calculate_variance(), 2),
            "std_deviation": round(self.calculate_std_deviation(), 2),
            "tail_risk_5pct": self.calculate_tail_risk(5.0),
            "success_tail_95pct": self.calculate_success_tail(95.0),
            "total_runs": len(self.results),
        }
    
    def get_percentiles(self, percentiles: List[float] = None) -> Dict[str, float]:
        """
        Calculate turn count percentiles.
        
        Args:
            percentiles: List of percentiles to calculate (default: [5, 25, 50, 75, 95])
            
        Returns:
            Dictionary mapping percentile to turn count
        """
        if percentiles is None:
            percentiles = [5, 25, 50, 75, 95]
        
        if not self.turns:
            return {f"p{int(p)}": 0.0 for p in percentiles}
        
        return {
            f"p{int(p)}": round(np.percentile(self.turns, p), 1)
            for p in percentiles
        }
    
    def get_confidence_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for win rate.
        
        Args:
            confidence: Confidence level (default: 0.95 for 95% CI)
            
        Returns:
            Tuple of (lower_bound, upper_bound) for win rate
        """
        if not self.wins:
            return (0.0, 0.0)
        
        n = len(self.wins)
        p = sum(self.wins) / n
        
        # Wilson score interval
        z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
        
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2*n)) / denominator
        margin = z * np.sqrt((p * (1-p) / n + z**2 / (4*n**2))) / denominator
        
        lower = max(0, center - margin) * 100
        upper = min(1, center + margin) * 100
        
        return (round(lower, 2), round(upper, 2))


def calculate_metrics_from_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function to calculate all metrics from results.
    
    Args:
        results: List of simulation run results
        
    Returns:
        Dictionary with all calculated metrics
    """
    metrics = SimulationMetrics(results)
    return metrics.get_all_metrics()


def compare_scenario_metrics(
    scenario_results: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Compare metrics across different scenarios.
    
    Args:
        scenario_results: Dictionary mapping scenario names to results lists
        
    Returns:
        Comparison dictionary
    """
    comparison = {}
    
    for scenario, results in scenario_results.items():
        metrics = SimulationMetrics(results)
        comparison[scenario] = metrics.get_all_metrics()
    
    # Add summary comparison
    comparison["summary"] = {
        "best_win_rate": max(
            comparison.keys(),
            key=lambda s: comparison[s]["win_rate"] if s != "summary" else 0
        ) if len(comparison) > 1 else None,
        "fastest_median": min(
            comparison.keys(),
            key=lambda s: comparison[s]["median_turns"] if s != "summary" else float('inf')
        ) if len(comparison) > 1 else None,
    }
    
    return comparison
