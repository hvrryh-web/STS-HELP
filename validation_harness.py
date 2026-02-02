"""
Validation harness for Slay the Spire simulation.
Implements calibration, reservoir sampling, and comparison to ground truth.

Resolution for G7: Statistical calibration and ground-truth validation.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import random

import numpy as np
import pandas as pd


@dataclass
class CalibrationResult:
    """Result of a calibration run."""
    character: str
    runs: int
    win_rate: float
    win_rate_ci: Tuple[float, float]
    median_turns: float
    mean_damage: float
    variance_damage: float
    bias: Optional[float] = None
    rmse: Optional[float] = None


class ReservoirSampler:
    """
    Reservoir sampler for streaming median computation.
    
    Resolution for G7: Reservoir sampling for medians.
    Uses Algorithm R for uniform sampling.
    """
    
    def __init__(self, k: int = 1000):
        """
        Initialize reservoir sampler.
        
        Args:
            k: Reservoir size.
        """
        self.k = k
        self.reservoir: List[float] = []
        self.n = 0
    
    def add(self, value: float) -> None:
        """Add a value to the reservoir."""
        self.n += 1
        
        if len(self.reservoir) < self.k:
            self.reservoir.append(value)
        else:
            # Random replacement
            j = random.randint(0, self.n - 1)
            if j < self.k:
                self.reservoir[j] = value
    
    def get_median(self) -> float:
        """Get approximate median from reservoir."""
        if not self.reservoir:
            return 0.0
        return float(np.median(self.reservoir))
    
    def get_percentile(self, p: float) -> float:
        """Get approximate percentile from reservoir."""
        if not self.reservoir:
            return 0.0
        return float(np.percentile(self.reservoir, p))


def wilson_score_interval(successes: int, trials: int, z: float = 1.96) -> Tuple[float, float]:
    """
    Compute Wilson score confidence interval for binomial proportion.
    
    Args:
        successes: Number of successes.
        trials: Total trials.
        z: Z-score for confidence level (1.96 for 95%).
    
    Returns:
        Tuple of (lower bound, upper bound).
    """
    if trials == 0:
        return (0.0, 1.0)
    
    p = successes / trials
    denominator = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * trials)) / trials) / denominator
    
    return (max(0, center - margin), min(1, center + margin))


def run_calibration(
    character: str,
    runs: int = 1000,
    seed: int = 42,
    ground_truth: Optional[Dict] = None
) -> CalibrationResult:
    """
    Run calibration for a single character.
    
    Args:
        character: Character name.
        runs: Number of runs.
        seed: Random seed.
        ground_truth: Optional ground truth data for comparison.
    
    Returns:
        CalibrationResult with statistics.
    """
    from seed_utils import make_child_generator
    
    # Import character engine
    if character == 'Ironclad':
        from ironclad_engine import simulate_run
    elif character == 'Silent':
        from silent_engine import simulate_run
    elif character == 'Defect':
        from defect_engine import simulate_run
    elif character == 'Watcher':
        from watcher_engine import simulate_run
    else:
        raise ValueError(f"Unknown character: {character}")
    
    # Initialize reservoir samplers
    turns_sampler = ReservoirSampler(k=1000)
    damage_sampler = ReservoirSampler(k=1000)
    
    # Run simulations
    wins = 0
    damages = []
    
    for i in range(runs):
        rng = make_child_generator(seed, character, 'none', i)
        result = simulate_run(rng)
        
        if result.win:
            wins += 1
        
        turns_sampler.add(result.turns)
        damage_sampler.add(result.damage_taken)
        damages.append(result.damage_taken)
    
    # Compute statistics
    win_rate = wins / runs
    win_rate_ci = wilson_score_interval(wins, runs)
    median_turns = turns_sampler.get_median()
    mean_damage = np.mean(damages)
    variance_damage = np.var(damages)
    
    result = CalibrationResult(
        character=character,
        runs=runs,
        win_rate=win_rate,
        win_rate_ci=win_rate_ci,
        median_turns=median_turns,
        mean_damage=mean_damage,
        variance_damage=variance_damage
    )
    
    # Compare to ground truth if provided
    if ground_truth and character in ground_truth:
        gt = ground_truth[character]
        if 'win_rate' in gt:
            result.bias = win_rate - gt['win_rate']
            result.rmse = abs(result.bias)
    
    return result


def run_full_calibration(
    characters: List[str] = None,
    runs_per_char: int = 1000,
    seed: int = 42,
    ground_truth_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, CalibrationResult]:
    """
    Run full calibration suite.
    
    Args:
        characters: List of characters to calibrate.
        runs_per_char: Runs per character.
        seed: Random seed.
        ground_truth_path: Path to ground truth JSON.
        output_path: Path to save calibration results.
    
    Returns:
        Dictionary of character to CalibrationResult.
    """
    if characters is None:
        characters = ['Ironclad', 'Silent', 'Defect', 'Watcher']
    
    # Load ground truth if provided
    ground_truth = None
    if ground_truth_path and Path(ground_truth_path).exists():
        with open(ground_truth_path, 'r') as f:
            ground_truth = json.load(f)
    
    results = {}
    
    for character in characters:
        print(f"Calibrating {character}...")
        result = run_calibration(character, runs_per_char, seed, ground_truth)
        results[character] = result
        
        print(f"  Win rate: {result.win_rate:.2%} ({result.win_rate_ci[0]:.2%} - {result.win_rate_ci[1]:.2%})")
        print(f"  Median turns: {result.median_turns:.1f}")
        print(f"  Mean damage: {result.mean_damage:.1f}")
        
        if result.bias is not None:
            print(f"  Bias vs ground truth: {result.bias:+.2%}")
    
    # Save results
    if output_path:
        output = {
            'timestamp': datetime.now().isoformat(),
            'seed': seed,
            'runs_per_char': runs_per_char,
            'results': {
                char: {
                    'win_rate': res.win_rate,
                    'win_rate_ci': list(res.win_rate_ci),
                    'median_turns': res.median_turns,
                    'mean_damage': res.mean_damage,
                    'variance_damage': res.variance_damage,
                    'bias': res.bias
                }
                for char, res in results.items()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nCalibration results saved to: {output_path}")
    
    return results


def validate_simulation_fidelity(
    parquet_path: str,
    expected_ranges: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Validate simulation fidelity against expected ranges.
    
    Args:
        parquet_path: Path to simulation results.
        expected_ranges: Dictionary of expected metric ranges.
    
    Returns:
        Validation report.
    """
    df = pd.read_parquet(parquet_path)
    
    if expected_ranges is None:
        # Default expected ranges (rough estimates)
        expected_ranges = {
            'win_rate': (0.3, 0.8),
            'mean_turns': (5, 30),
            'mean_damage': (10, 60)
        }
    
    win_rate = df['win'].mean()
    mean_turns = df['turns'].mean()
    mean_damage = df['damage_taken'].mean()
    
    issues = []
    
    if not expected_ranges['win_rate'][0] <= win_rate <= expected_ranges['win_rate'][1]:
        issues.append(f"Win rate {win_rate:.2%} outside expected range {expected_ranges['win_rate']}")
    
    if not expected_ranges['mean_turns'][0] <= mean_turns <= expected_ranges['mean_turns'][1]:
        issues.append(f"Mean turns {mean_turns:.1f} outside expected range {expected_ranges['mean_turns']}")
    
    if not expected_ranges['mean_damage'][0] <= mean_damage <= expected_ranges['mean_damage'][1]:
        issues.append(f"Mean damage {mean_damage:.1f} outside expected range {expected_ranges['mean_damage']}")
    
    return {
        'passed': len(issues) == 0,
        'metrics': {
            'win_rate': win_rate,
            'mean_turns': mean_turns,
            'mean_damage': mean_damage
        },
        'issues': issues
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='STS Simulation Validation Harness')
    parser.add_argument('--characters', nargs='+', default=['Ironclad'],
                        help='Characters to calibrate')
    parser.add_argument('--runs', type=int, default=1000,
                        help='Runs per character')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--ground-truth', type=str,
                        help='Path to ground truth JSON')
    parser.add_argument('--output', type=str, default='calibration_results.json',
                        help='Output path for results')
    
    args = parser.parse_args()
    
    run_full_calibration(
        characters=args.characters,
        runs_per_char=args.runs,
        seed=args.seed,
        ground_truth_path=args.ground_truth,
        output_path=args.output
    )
