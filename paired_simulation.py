"""
Paired-seed variance reduction for forced-action Monte Carlo.

Per critical review Section 2.2:
Common Random Numbers (CRN) approach for decision evaluation.
By using paired simulations with identical random streams except for the action,
we dramatically reduce variance and can detect smaller improvements with fewer runs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Callable, Any, Optional
import numpy as np

from seed_utils import make_child_generator

# Optional scipy import for statistical functions
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    scipy_stats = None


@dataclass
class PairedSimulationResult:
    """
    Result of a paired simulation (with and without action).
    
    Attributes:
        base_result: Result without the action.
        action_result: Result with the action.
        action_value: Estimated value of taking the action.
        variance_reduced: Whether variance reduction was applied.
    """
    base_result: Dict[str, Any]
    action_result: Dict[str, Any]
    action_value: float
    variance_reduced: bool = True
    
    @property
    def raw_difference(self) -> float:
        """Raw difference in reward between action and no-action."""
        base_reward = self._compute_reward(self.base_result)
        action_reward = self._compute_reward(self.action_result)
        return action_reward - base_reward
    
    def _compute_reward(self, result: Dict) -> float:
        """Compute reward from result dict."""
        win = result.get('win', False)
        damage = result.get('damage_taken', 0)
        turns = result.get('turns', 50)
        
        # Default reward function: win bonus - damage penalty - turn penalty
        reward = (100 if win else 0) - damage - (turns * 0.5)
        return reward


@dataclass
class PairedSeedSet:
    """
    A set of seeds for paired simulation.
    
    Attributes:
        root_seed: Root seed.
        enemy_intent_seed: Seed for enemy intent randomness.
        shuffle_seed: Seed for deck shuffling.
        relic_seed: Seed for relic/reward drops.
        event_seed: Seed for event randomness.
    """
    root_seed: int
    enemy_intent_seed: int
    shuffle_seed: int
    relic_seed: int
    event_seed: int
    
    @classmethod
    def from_root(cls, root_seed: int, run_index: int) -> 'PairedSeedSet':
        """
        Create paired seed set from root seed and run index.
        
        Args:
            root_seed: Root seed.
            run_index: Index of this run.
        
        Returns:
            PairedSeedSet with deterministic child seeds.
        """
        rng = np.random.default_rng(root_seed + run_index * 1000003)
        
        return cls(
            root_seed=root_seed,
            enemy_intent_seed=int(rng.integers(0, 2**31)),
            shuffle_seed=int(rng.integers(0, 2**31)),
            relic_seed=int(rng.integers(0, 2**31)),
            event_seed=int(rng.integers(0, 2**31))
        )


def run_paired_simulation(
    simulate_fn: Callable,
    seed_set: PairedSeedSet,
    base_action: Any,
    test_action: Any,
    context: Dict[str, Any] = None
) -> PairedSimulationResult:
    """
    Run a paired simulation comparing two actions.
    
    Uses Common Random Numbers for variance reduction:
    - Same enemy intent stream
    - Same shuffle order
    - Same event/reward rolls
    Only the action differs.
    
    Args:
        simulate_fn: Simulation function that takes (rng, action, context).
        seed_set: Paired seed set.
        base_action: Action for base case (e.g., "skip" or "defend").
        test_action: Action to test.
        context: Additional context for simulation.
    
    Returns:
        PairedSimulationResult with both outcomes and value difference.
    """
    if context is None:
        context = {}
    
    # Create RNG for base simulation
    base_rng = create_paired_rng(seed_set)
    base_result = simulate_fn(base_rng, base_action, context)
    
    # Create IDENTICAL RNG for test simulation
    test_rng = create_paired_rng(seed_set)
    test_result = simulate_fn(test_rng, test_action, context)
    
    # Compute action value
    paired_result = PairedSimulationResult(
        base_result=base_result,
        action_result=test_result,
        action_value=0.0  # Will be computed
    )
    paired_result.action_value = paired_result.raw_difference
    
    return paired_result


def create_paired_rng(seed_set: PairedSeedSet) -> np.random.Generator:
    """
    Create a random generator from paired seed set.
    
    Args:
        seed_set: Paired seed set.
    
    Returns:
        numpy random Generator.
    """
    # Combine all seeds for consistent initial state
    combined = (
        seed_set.root_seed ^
        (seed_set.enemy_intent_seed << 1) ^
        (seed_set.shuffle_seed << 2) ^
        (seed_set.relic_seed << 3) ^
        (seed_set.event_seed << 4)
    )
    return np.random.default_rng(combined)


def run_batch_paired_evaluations(
    simulate_fn: Callable,
    root_seed: int,
    actions_to_evaluate: List[Tuple[Any, Any]],
    num_pairs: int = 100,
    context: Dict[str, Any] = None
) -> Dict[str, Dict[str, float]]:
    """
    Run batch paired evaluations for multiple action comparisons.
    
    Args:
        simulate_fn: Simulation function.
        root_seed: Root seed.
        actions_to_evaluate: List of (base_action, test_action) tuples.
        num_pairs: Number of paired simulations per action.
        context: Additional context.
    
    Returns:
        Dictionary mapping action description to evaluation stats.
    """
    if context is None:
        context = {}
    
    results = {}
    
    for base_action, test_action in actions_to_evaluate:
        action_key = f"{base_action} -> {test_action}"
        values = []
        
        for i in range(num_pairs):
            seed_set = PairedSeedSet.from_root(root_seed, i)
            paired_result = run_paired_simulation(
                simulate_fn,
                seed_set,
                base_action,
                test_action,
                context
            )
            values.append(paired_result.action_value)
        
        # Compute statistics
        values_arr = np.array(values)
        results[action_key] = {
            'mean': float(np.mean(values_arr)),
            'std': float(np.std(values_arr)),
            'sem': float(np.std(values_arr) / np.sqrt(len(values_arr))),
            'min': float(np.min(values_arr)),
            'max': float(np.max(values_arr)),
            'positive_rate': float(np.mean(values_arr > 0)),
            'n_pairs': num_pairs
        }
    
    return results


def compute_required_sample_size(
    effect_size: float,
    variance: float,
    alpha: float = 0.05,
    power: float = 0.8
) -> int:
    """
    Compute required sample size for detecting an effect.
    
    Per critical review Section 2.2:
    With paired seeds, variance is reduced, so fewer samples needed.
    
    Args:
        effect_size: Minimum effect size to detect.
        variance: Estimated variance of the difference.
        alpha: Significance level.
        power: Desired power.
    
    Returns:
        Required number of paired samples.
    """
    if not HAS_SCIPY:
        raise ImportError("scipy is required for compute_required_sample_size")
    
    # Z-scores for alpha and power
    z_alpha = scipy_stats.norm.ppf(1 - alpha / 2)
    z_beta = scipy_stats.norm.ppf(power)
    
    # Sample size formula for paired t-test
    n = ((z_alpha + z_beta) ** 2 * variance) / (effect_size ** 2)
    
    return int(np.ceil(n))


class ActionEvaluator:
    """
    Evaluator for action comparison using paired simulations.
    
    Usage:
        evaluator = ActionEvaluator(simulate_fn, root_seed=42)
        value, ci = evaluator.evaluate_action("Attack", "Defend", n_pairs=100)
        if value > 0 and ci[0] > 0:
            print("Attack is significantly better than Defend")
    """
    
    def __init__(
        self,
        simulate_fn: Callable,
        root_seed: int,
        context: Dict[str, Any] = None
    ):
        """
        Initialize evaluator.
        
        Args:
            simulate_fn: Simulation function.
            root_seed: Root seed for reproducibility.
            context: Additional context for simulations.
        """
        self.simulate_fn = simulate_fn
        self.root_seed = root_seed
        self.context = context or {}
        self._cache: Dict[str, PairedSimulationResult] = {}
    
    def evaluate_action(
        self,
        test_action: Any,
        base_action: Any = "pass",
        n_pairs: int = 100,
        confidence: float = 0.95
    ) -> Tuple[float, Tuple[float, float]]:
        """
        Evaluate an action against a base action.
        
        Args:
            test_action: Action to evaluate.
            base_action: Base action for comparison.
            n_pairs: Number of paired simulations.
            confidence: Confidence level for interval.
        
        Returns:
            Tuple of (mean_value, (lower_ci, upper_ci)).
        """
        values = []
        
        for i in range(n_pairs):
            seed_set = PairedSeedSet.from_root(self.root_seed, i)
            result = run_paired_simulation(
                self.simulate_fn,
                seed_set,
                base_action,
                test_action,
                self.context
            )
            values.append(result.action_value)
        
        values_arr = np.array(values)
        mean = np.mean(values_arr)
        sem = np.std(values_arr) / np.sqrt(n_pairs)
        
        # Compute confidence interval
        if HAS_SCIPY:
            t_crit = scipy_stats.t.ppf((1 + confidence) / 2, n_pairs - 1)
        else:
            # Fallback to z-score approximation for large samples
            t_crit = 1.96 if confidence == 0.95 else 2.576  # Approximate for 95%/99%
        ci = (mean - t_crit * sem, mean + t_crit * sem)
        
        return float(mean), (float(ci[0]), float(ci[1]))
    
    def rank_actions(
        self,
        actions: List[Any],
        base_action: Any = "pass",
        n_pairs: int = 100
    ) -> List[Tuple[Any, float, Tuple[float, float]]]:
        """
        Rank multiple actions by their value.
        
        Args:
            actions: List of actions to evaluate.
            base_action: Base action for comparison.
            n_pairs: Number of paired simulations per action.
        
        Returns:
            List of (action, mean_value, ci) sorted by mean_value descending.
        """
        results = []
        
        for action in actions:
            mean, ci = self.evaluate_action(action, base_action, n_pairs)
            results.append((action, mean, ci))
        
        # Sort by mean value descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results
