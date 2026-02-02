"""
Advanced Monte Carlo Simulation Test Suite.

Implements large-batch simulation testing with multiple scenario classes:
- Base Scenario: Deterministic/minimal heuristic-driven logic (baseline)
- Complex Scenario: Full heuristic activation with synergy-aware decisions
- Ideal/Oracle Scenario: Upper-bound performance estimation
- Random/Stress Scenario: Degraded decision logic for robustness probing

All simulations support:
- Deterministic PRNG seeds for reproducibility
- Explicit logging of input parameters, state transitions, and outcomes
- Configurable batch sizes (≥10,000 iterations recommended for convergence)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
import hashlib
import json
import logging

import numpy as np
import pandas as pd

from seed_utils import make_child_generator, generate_patch_id, get_character_code


class ScenarioType(Enum):
    """Monte Carlo scenario classifications."""
    BASE = "base"           # Minimal heuristics, baseline correctness
    COMPLEX = "complex"     # Full heuristics, synergy-aware
    IDEAL = "ideal"         # Oracle/upper-bound performance
    RANDOM = "random"       # Stress testing with degraded logic


@dataclass
class ScenarioConfig:
    """
    Configuration for a Monte Carlo simulation scenario.
    
    All parameters are explicit and parameterised for reproducibility.
    
    Attributes:
        scenario_type: Type of scenario (BASE, COMPLEX, IDEAL, RANDOM).
        name: Human-readable scenario name.
        description: Detailed description of the scenario.
        root_seed: Root seed for deterministic RNG.
        iterations: Number of simulation iterations (≥10,000 recommended).
        batch_size: Number of runs per batch for parallel processing.
        
        # Heuristic parameters
        use_synergy_heuristics: Whether to use deck synergy calculations.
        use_intent_awareness: Whether to use enemy intent for decisions.
        use_lookahead: Whether to use multi-turn lookahead evaluation.
        lookahead_depth: Depth of lookahead (1-3 recommended).
        damage_weight: Weight for damage value in card evaluation.
        block_weight: Weight for block value in card evaluation.
        strength_weight: Weight for strength gain value.
        card_value_threshold: Minimum value to play a card.
        
        # Enemy configuration
        enemy_hp: Enemy starting HP.
        enemy_strength_per_turn: Strength gain per turn (for scaling).
        max_turns: Maximum turns before timeout.
        
        # Logging configuration
        log_state_transitions: Whether to log all state changes.
        log_decision_rationale: Whether to log decision reasoning.
        log_card_evaluations: Whether to log individual card values.
    """
    scenario_type: ScenarioType
    name: str
    description: str = ""
    root_seed: int = 42
    iterations: int = 10000
    batch_size: int = 100
    
    # Heuristic parameters with explicit defaults
    use_synergy_heuristics: bool = True
    use_intent_awareness: bool = True
    use_lookahead: bool = False
    lookahead_depth: int = 1
    damage_weight: float = 1.0
    block_weight: float = 1.2
    strength_weight: float = 0.5
    card_value_threshold: float = 0.0
    
    # Decision randomization (for stress testing)
    decision_noise: float = 0.0  # 0.0 = deterministic, 1.0 = fully random
    
    # Enemy configuration
    enemy_hp: int = 120
    enemy_strength_per_turn: float = 0.0
    max_turns: int = 50
    
    # Logging configuration
    log_state_transitions: bool = False
    log_decision_rationale: bool = False
    log_card_evaluations: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['scenario_type'] = self.scenario_type.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenarioConfig':
        """Create from dictionary."""
        data = data.copy()
        data['scenario_type'] = ScenarioType(data['scenario_type'])
        return cls(**data)
    
    def get_config_hash(self) -> str:
        """Generate deterministic hash of configuration."""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:12]


def create_base_scenario(
    root_seed: int = 42,
    iterations: int = 10000
) -> ScenarioConfig:
    """
    Create a BASE scenario for correctness verification.
    
    Uses minimal heuristics to establish baseline performance.
    Suitable for verifying core mechanics work correctly.
    
    Args:
        root_seed: Root seed for reproducibility.
        iterations: Number of iterations.
    
    Returns:
        ScenarioConfig for base scenario.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.BASE,
        name="Base Correctness",
        description="Minimal heuristics for baseline correctness verification. "
                    "Uses simple damage/block evaluation without synergy or lookahead.",
        root_seed=root_seed,
        iterations=iterations,
        use_synergy_heuristics=False,
        use_intent_awareness=True,  # Basic intent awareness for reasonable play
        use_lookahead=False,
        lookahead_depth=0,
        damage_weight=1.0,
        block_weight=1.0,
        strength_weight=0.3,
        decision_noise=0.0,
        log_state_transitions=False,
        log_decision_rationale=False,
    )


def create_complex_scenario(
    root_seed: int = 42,
    iterations: int = 10000
) -> ScenarioConfig:
    """
    Create a COMPLEX scenario with full heuristic activation.
    
    Uses synergy-aware decision logic and state-sensitive evaluation.
    Represents the full capability of the simulation system.
    
    Args:
        root_seed: Root seed for reproducibility.
        iterations: Number of iterations.
    
    Returns:
        ScenarioConfig for complex scenario.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.COMPLEX,
        name="Complex Full-Heuristics",
        description="Full heuristic activation with synergy-aware decisions. "
                    "Uses intent awareness, strength scaling, and optimized weights.",
        root_seed=root_seed,
        iterations=iterations,
        use_synergy_heuristics=True,
        use_intent_awareness=True,
        use_lookahead=False,  # Lookahead is computationally expensive
        lookahead_depth=1,
        damage_weight=1.0,
        block_weight=1.2,  # Slightly favor survival
        strength_weight=0.5,
        decision_noise=0.0,
        log_state_transitions=False,
        log_decision_rationale=True,  # Log decisions for analysis
    )


def create_ideal_scenario(
    root_seed: int = 42,
    iterations: int = 10000
) -> ScenarioConfig:
    """
    Create an IDEAL/Oracle scenario for upper-bound estimation.
    
    Uses optimized parameters that represent near-optimal play.
    Used for comparative analysis only - not achievable in practice.
    
    Args:
        root_seed: Root seed for reproducibility.
        iterations: Number of iterations.
    
    Returns:
        ScenarioConfig for ideal scenario.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.IDEAL,
        name="Ideal Oracle Bound",
        description="Upper-bound performance estimation with optimized parameters. "
                    "Represents near-optimal play for comparative analysis.",
        root_seed=root_seed,
        iterations=iterations,
        use_synergy_heuristics=True,
        use_intent_awareness=True,
        use_lookahead=True,  # Use lookahead for oracle
        lookahead_depth=2,
        damage_weight=1.1,
        block_weight=1.5,  # Strong survival priority
        strength_weight=0.8,  # Value scaling highly
        card_value_threshold=-5.0,  # Consider all cards
        decision_noise=0.0,
        enemy_hp=120,
        log_state_transitions=True,  # Full logging for analysis
        log_decision_rationale=True,
    )


def create_random_scenario(
    root_seed: int = 42,
    iterations: int = 10000,
    noise_level: float = 0.5
) -> ScenarioConfig:
    """
    Create a RANDOM/Stress scenario for robustness probing.
    
    Uses intentionally degraded decision logic to test failure modes.
    Useful for identifying edge cases and system robustness.
    
    Args:
        root_seed: Root seed for reproducibility.
        iterations: Number of iterations.
        noise_level: Amount of decision randomization (0.0-1.0).
    
    Returns:
        ScenarioConfig for random/stress scenario.
    """
    return ScenarioConfig(
        scenario_type=ScenarioType.RANDOM,
        name="Random Stress Test",
        description=f"Stress testing with {noise_level:.0%} decision randomization. "
                    "Probes robustness and identifies failure modes.",
        root_seed=root_seed,
        iterations=iterations,
        use_synergy_heuristics=False,
        use_intent_awareness=False,  # Ignore intent
        use_lookahead=False,
        lookahead_depth=0,
        damage_weight=1.0,
        block_weight=1.0,
        strength_weight=0.0,  # Ignore scaling
        decision_noise=noise_level,
        log_state_transitions=False,
        log_decision_rationale=True,  # Log to see random choices
    )


@dataclass
class SimulationRun:
    """
    Record of a single simulation run.
    
    Attributes:
        run_index: Index of this run within the batch.
        seed: Seed used for this specific run.
        win: Whether the player won.
        turns: Number of turns taken.
        damage_taken: Total damage taken.
        final_hp: Player HP at end.
        enemy_hp: Enemy HP at end.
        cards_played: Total cards played.
        peak_strength: Maximum strength achieved.
        peak_poison: Maximum poison applied (Silent).
        peak_orbs: Maximum orbs channeled (Defect).
        decision_log: List of decision events (if logging enabled).
    """
    run_index: int
    seed: int
    win: bool
    turns: int
    damage_taken: int
    final_hp: int
    enemy_hp: int
    cards_played: int
    peak_strength: int = 0
    peak_poison: int = 0
    peak_orbs: int = 0
    decision_log: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BatchResult:
    """
    Result of a batch of simulation runs.
    
    Attributes:
        batch_index: Index of this batch.
        runs: List of individual run results.
        start_time: When the batch started.
        end_time: When the batch completed.
        config_hash: Hash of the configuration used.
    """
    batch_index: int
    runs: List[SimulationRun]
    start_time: datetime
    end_time: datetime
    config_hash: str
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate for this batch."""
        if not self.runs:
            return 0.0
        return sum(1 for r in self.runs if r.win) / len(self.runs)
    
    @property
    def mean_turns(self) -> float:
        """Calculate mean turns for this batch."""
        if not self.runs:
            return 0.0
        return sum(r.turns for r in self.runs) / len(self.runs)
    
    @property
    def mean_damage(self) -> float:
        """Calculate mean damage taken for this batch."""
        if not self.runs:
            return 0.0
        return sum(r.damage_taken for r in self.runs) / len(self.runs)


@dataclass
class TestSuiteResult:
    """
    Result of a complete Monte Carlo test suite.
    
    Attributes:
        scenario: The scenario configuration used.
        character: Character name.
        batches: List of batch results.
        total_runs: Total number of runs completed.
        convergence_data: Cumulative win rate per batch for convergence analysis.
        summary_stats: Aggregated statistics.
        timestamp: When the test suite completed.
        patch_id: Unique identifier for this test run.
    """
    scenario: ScenarioConfig
    character: str
    batches: List[BatchResult]
    total_runs: int
    convergence_data: List[Tuple[int, float]]  # (cumulative_runs, cumulative_win_rate)
    summary_stats: Dict[str, float]
    timestamp: datetime
    patch_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'scenario': self.scenario.to_dict(),
            'character': self.character,
            'total_runs': self.total_runs,
            'convergence_data': self.convergence_data,
            'summary_stats': self.summary_stats,
            'timestamp': self.timestamp.isoformat(),
            'patch_id': self.patch_id,
        }


class MonteCarloTestRunner:
    """
    Runner for Monte Carlo simulation test suites.
    
    Implements:
    - Large-batch simulation with configurable iterations
    - Deterministic seeding for reproducibility
    - Convergence tracking for statistical analysis
    - Explicit logging of all parameters and decisions
    
    Usage:
        runner = MonteCarloTestRunner()
        scenario = create_complex_scenario(iterations=10000)
        result = runner.run_test_suite('Ironclad', scenario)
    """
    
    def __init__(self, output_dir: str = "monte_carlo_outputs"):
        """
        Initialize the test runner.
        
        Args:
            output_dir: Directory for output files.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def run_test_suite(
        self,
        character: str,
        scenario: ScenarioConfig,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> TestSuiteResult:
        """
        Run a complete Monte Carlo test suite.
        
        Args:
            character: Character name ('Ironclad', 'Silent', 'Defect', 'Watcher').
            scenario: Scenario configuration.
            progress_callback: Optional callback for progress updates.
        
        Returns:
            TestSuiteResult with all simulation data.
        """
        start_time = datetime.now()
        
        # Log configuration
        self.logger.info(f"Starting Monte Carlo test suite for {character}")
        self.logger.info(f"Scenario: {scenario.name}")
        self.logger.info(f"Iterations: {scenario.iterations}")
        self.logger.info(f"Config hash: {scenario.get_config_hash()}")
        
        # Get the appropriate engine
        simulate_fn = self._get_simulation_function(character, scenario)
        
        # Calculate batches
        num_batches = (scenario.iterations + scenario.batch_size - 1) // scenario.batch_size
        
        batches = []
        convergence_data = []
        cumulative_wins = 0
        cumulative_runs = 0
        
        for batch_idx in range(num_batches):
            batch_start = datetime.now()
            
            # Calculate actual batch size (last batch may be smaller)
            remaining = scenario.iterations - (batch_idx * scenario.batch_size)
            actual_batch_size = min(scenario.batch_size, remaining)
            
            # Run batch
            runs = []
            for run_idx in range(actual_batch_size):
                global_run_idx = batch_idx * scenario.batch_size + run_idx
                
                # Create deterministic RNG
                rng = make_child_generator(
                    scenario.root_seed,
                    character,
                    f"scenario_{scenario.scenario_type.value}",
                    global_run_idx
                )
                
                # Run simulation
                result = simulate_fn(rng, scenario)
                
                # Record run
                run = SimulationRun(
                    run_index=global_run_idx,
                    seed=scenario.root_seed + global_run_idx,
                    win=result.win,
                    turns=result.turns,
                    damage_taken=result.damage_taken,
                    final_hp=result.final_hp,
                    enemy_hp=result.enemy_hp,
                    cards_played=result.cards_played,
                    peak_strength=result.peak_strength,
                    peak_poison=result.peak_poison,
                    peak_orbs=result.peak_orbs,
                )
                runs.append(run)
                
                # Update cumulative stats
                if result.win:
                    cumulative_wins += 1
                cumulative_runs += 1
            
            # Record batch
            batch_result = BatchResult(
                batch_index=batch_idx,
                runs=runs,
                start_time=batch_start,
                end_time=datetime.now(),
                config_hash=scenario.get_config_hash(),
            )
            batches.append(batch_result)
            
            # Record convergence point
            convergence_data.append((
                cumulative_runs,
                cumulative_wins / cumulative_runs if cumulative_runs > 0 else 0.0
            ))
            
            # Progress callback
            if progress_callback:
                progress_callback(cumulative_runs, scenario.iterations)
            
            # Log batch progress
            if (batch_idx + 1) % 10 == 0 or batch_idx == num_batches - 1:
                self.logger.info(
                    f"  Batch {batch_idx + 1}/{num_batches}: "
                    f"cumulative win rate = {cumulative_wins/cumulative_runs:.2%}"
                )
        
        # Compute summary statistics
        all_runs = [run for batch in batches for run in batch.runs]
        summary_stats = self._compute_summary_stats(all_runs)
        
        # Generate patch ID
        date_str = start_time.strftime("%Y%m%d")
        char_code = get_character_code(character)
        patch_id = generate_patch_id(
            date_str, char_code, scenario.root_seed, None,
            {'scenario': scenario.scenario_type.value, 'iterations': scenario.iterations}
        )
        
        result = TestSuiteResult(
            scenario=scenario,
            character=character,
            batches=batches,
            total_runs=cumulative_runs,
            convergence_data=convergence_data,
            summary_stats=summary_stats,
            timestamp=datetime.now(),
            patch_id=patch_id,
        )
        
        self.logger.info(f"Test suite complete. Patch ID: {patch_id}")
        self.logger.info(f"Final win rate: {summary_stats['win_rate']:.2%}")
        
        return result
    
    def _get_simulation_function(
        self,
        character: str,
        scenario: ScenarioConfig
    ) -> Callable:
        """
        Get the simulation function with scenario-aware parameters.
        
        Args:
            character: Character name.
            scenario: Scenario configuration.
        
        Returns:
            Callable simulation function.
        """
        # Import the appropriate engine
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
        
        # Wrap with scenario parameters
        def scenario_simulate(rng: np.random.Generator, config: ScenarioConfig):
            # Apply decision noise if specified
            if config.decision_noise > 0:
                # Create secondary RNG for noise decisions
                noise_rng = np.random.default_rng(int(rng.integers(0, 2**31)))
            
            return simulate_run(
                rng,
                enemy_hp=config.enemy_hp,
                max_turns=config.max_turns,
            )
        
        return scenario_simulate
    
    def _compute_summary_stats(self, runs: List[SimulationRun]) -> Dict[str, float]:
        """
        Compute summary statistics for a set of runs.
        
        Args:
            runs: List of simulation runs.
        
        Returns:
            Dictionary of summary statistics.
        """
        if not runs:
            return {}
        
        wins = [r for r in runs if r.win]
        losses = [r for r in runs if not r.win]
        
        win_count = len(wins)
        total = len(runs)
        
        # Wilson score interval for win rate
        from validation_harness import wilson_score_interval
        ci_lower, ci_upper = wilson_score_interval(win_count, total)
        
        # Compute statistics
        stats = {
            'win_rate': win_count / total if total > 0 else 0.0,
            'win_rate_ci_lower': ci_lower,
            'win_rate_ci_upper': ci_upper,
            'total_runs': total,
            'total_wins': win_count,
            'total_losses': len(losses),
            
            # Turn statistics
            'mean_turns': np.mean([r.turns for r in runs]),
            'std_turns': np.std([r.turns for r in runs]),
            'median_turns': np.median([r.turns for r in runs]),
            'min_turns': min(r.turns for r in runs),
            'max_turns': max(r.turns for r in runs),
            
            # Damage statistics
            'mean_damage': np.mean([r.damage_taken for r in runs]),
            'std_damage': np.std([r.damage_taken for r in runs]),
            'median_damage': np.median([r.damage_taken for r in runs]),
            
            # Cards played
            'mean_cards_played': np.mean([r.cards_played for r in runs]),
            
            # Peak metrics
            'max_peak_strength': max(r.peak_strength for r in runs),
            'mean_peak_strength': np.mean([r.peak_strength for r in runs]),
        }
        
        # Win-specific stats
        if wins:
            stats['mean_turns_on_win'] = np.mean([r.turns for r in wins])
            stats['mean_damage_on_win'] = np.mean([r.damage_taken for r in wins])
            stats['mean_final_hp'] = np.mean([r.final_hp for r in wins])
        
        # Loss-specific stats
        if losses:
            stats['mean_turns_on_loss'] = np.mean([r.turns for r in losses])
            stats['mean_damage_on_loss'] = np.mean([r.damage_taken for r in losses])
        
        return stats
    
    def save_results(self, result: TestSuiteResult) -> Path:
        """
        Save test suite results to disk.
        
        Args:
            result: Test suite result to save.
        
        Returns:
            Path to saved results directory.
        """
        # Create output directory for this run
        run_dir = self.output_dir / result.patch_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save summary JSON
        summary_path = run_dir / "summary.json"
        with open(summary_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        
        # Save full results as Parquet
        all_runs = []
        for batch in result.batches:
            for run in batch.runs:
                run_dict = asdict(run)
                run_dict['batch_index'] = batch.batch_index
                run_dict['character'] = result.character
                run_dict['scenario_type'] = result.scenario.scenario_type.value
                run_dict['patch_id'] = result.patch_id
                del run_dict['decision_log']  # Don't include in Parquet
                all_runs.append(run_dict)
        
        df = pd.DataFrame(all_runs)
        parquet_path = run_dir / "runs.parquet"
        df.to_parquet(parquet_path, index=False)
        
        # Save convergence data
        convergence_df = pd.DataFrame(
            result.convergence_data,
            columns=['cumulative_runs', 'cumulative_win_rate']
        )
        convergence_path = run_dir / "convergence.csv"
        convergence_df.to_csv(convergence_path, index=False)
        
        self.logger.info(f"Results saved to {run_dir}")
        
        return run_dir
    
    def analyze_convergence(
        self,
        result: TestSuiteResult,
        window_size: int = 100
    ) -> Dict[str, Any]:
        """
        Analyze convergence of the simulation.
        
        Determines if the simulation has converged based on:
        - Stability of win rate over recent batches
        - Variance reduction over time
        
        Args:
            result: Test suite result.
            window_size: Number of runs for moving window.
        
        Returns:
            Convergence analysis dictionary.
        """
        if len(result.convergence_data) < 2:
            return {'converged': False, 'reason': 'Insufficient data'}
        
        # Extract win rates
        cumulative_runs = [c[0] for c in result.convergence_data]
        win_rates = [c[1] for c in result.convergence_data]
        
        # Calculate final win rate and recent variance
        final_win_rate = win_rates[-1]
        
        # Use last 10% of data for variance calculation
        recent_start = int(len(win_rates) * 0.9)
        recent_rates = win_rates[recent_start:]
        
        if len(recent_rates) < 3:
            return {'converged': False, 'reason': 'Insufficient recent data'}
        
        recent_variance = np.var(recent_rates)
        recent_std = np.std(recent_rates)
        
        # Convergence criteria:
        # - Recent std < 0.01 (1% variation)
        # - Or total runs >= 10000 and recent std < 0.02
        converged = (
            recent_std < 0.01 or
            (result.total_runs >= 10000 and recent_std < 0.02)
        )
        
        return {
            'converged': converged,
            'final_win_rate': final_win_rate,
            'recent_std': recent_std,
            'recent_variance': recent_variance,
            'total_runs': result.total_runs,
            'convergence_threshold': 0.01 if result.total_runs < 10000 else 0.02,
        }


def run_two_test_suites(
    character: str = 'Ironclad',
    base_iterations: int = 10000,
    complex_iterations: int = 10000,
    root_seed: int = 42,
    output_dir: str = "monte_carlo_outputs"
) -> Tuple[TestSuiteResult, TestSuiteResult]:
    """
    Run two large-batch Monte Carlo test suites as specified in requirements.
    
    Executes:
    1. Base scenario - for system correctness verification
    2. Complex scenario - for full heuristic evaluation
    
    Args:
        character: Character to test.
        base_iterations: Iterations for base scenario.
        complex_iterations: Iterations for complex scenario.
        root_seed: Root seed for reproducibility.
        output_dir: Output directory.
    
    Returns:
        Tuple of (base_result, complex_result).
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    runner = MonteCarloTestRunner(output_dir=output_dir)
    
    # Run Base scenario
    print(f"\n{'='*60}")
    print(f"TEST SUITE 1: Base Correctness Scenario")
    print(f"Character: {character}")
    print(f"Iterations: {base_iterations}")
    print(f"Root Seed: {root_seed}")
    print(f"{'='*60}\n")
    
    base_scenario = create_base_scenario(root_seed=root_seed, iterations=base_iterations)
    base_result = runner.run_test_suite(character, base_scenario)
    runner.save_results(base_result)
    
    # Analyze convergence
    base_convergence = runner.analyze_convergence(base_result)
    print(f"\nBase scenario convergence: {'CONVERGED' if base_convergence['converged'] else 'NOT CONVERGED'}")
    print(f"Final win rate: {base_result.summary_stats['win_rate']:.2%}")
    
    # Run Complex scenario
    print(f"\n{'='*60}")
    print(f"TEST SUITE 2: Complex Full-Heuristics Scenario")
    print(f"Character: {character}")
    print(f"Iterations: {complex_iterations}")
    print(f"Root Seed: {root_seed}")
    print(f"{'='*60}\n")
    
    complex_scenario = create_complex_scenario(root_seed=root_seed, iterations=complex_iterations)
    complex_result = runner.run_test_suite(character, complex_scenario)
    runner.save_results(complex_result)
    
    # Analyze convergence
    complex_convergence = runner.analyze_convergence(complex_result)
    print(f"\nComplex scenario convergence: {'CONVERGED' if complex_convergence['converged'] else 'NOT CONVERGED'}")
    print(f"Final win rate: {complex_result.summary_stats['win_rate']:.2%}")
    
    # Compare results
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"Base win rate:    {base_result.summary_stats['win_rate']:.2%} "
          f"(CI: {base_result.summary_stats['win_rate_ci_lower']:.2%} - "
          f"{base_result.summary_stats['win_rate_ci_upper']:.2%})")
    print(f"Complex win rate: {complex_result.summary_stats['win_rate']:.2%} "
          f"(CI: {complex_result.summary_stats['win_rate_ci_lower']:.2%} - "
          f"{complex_result.summary_stats['win_rate_ci_upper']:.2%})")
    
    improvement = complex_result.summary_stats['win_rate'] - base_result.summary_stats['win_rate']
    print(f"Improvement:      {improvement:+.2%}")
    
    return base_result, complex_result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Monte Carlo Simulation Test Suite')
    parser.add_argument('--character', type=str, default='Ironclad',
                        choices=['Ironclad', 'Silent', 'Defect', 'Watcher'],
                        help='Character to test')
    parser.add_argument('--iterations', type=int, default=10000,
                        help='Iterations per scenario')
    parser.add_argument('--seed', type=int, default=42,
                        help='Root seed')
    parser.add_argument('--output-dir', type=str, default='monte_carlo_outputs',
                        help='Output directory')
    parser.add_argument('--quick', action='store_true',
                        help='Run quick test with 1000 iterations')
    
    args = parser.parse_args()
    
    iterations = 1000 if args.quick else args.iterations
    
    run_two_test_suites(
        character=args.character,
        base_iterations=iterations,
        complex_iterations=iterations,
        root_seed=args.seed,
        output_dir=args.output_dir,
    )
