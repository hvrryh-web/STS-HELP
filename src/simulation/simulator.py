"""
Monte Carlo simulation engine for Slay the Spire.

This module provides the main simulation class that supports
4 scenario types: BASE, COMPLEX, IDEAL, and RANDOM.

It integrates with the existing monte_carlo_suite.py functionality
while providing a clean API for running simulations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import numpy as np
import json

# Import from existing codebase
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from monte_carlo_suite import (
    ScenarioType,
    ScenarioConfig,
    MonteCarloTestRunner,
    create_base_scenario,
    create_complex_scenario,
    create_ideal_scenario,
    create_random_scenario,
)


class MonteCarloSimulator:
    """
    Main Monte Carlo simulation engine.
    
    Supports 4 scenario types:
    - BASE: Deterministic behavior, no heuristics
    - COMPLEX: Synergy-driven decision trees
    - IDEAL: Perfect-play oracle model
    - RANDOM: Stress-test for robustness
    
    Attributes:
        root_seed: Root seed for reproducibility
        iterations: Number of simulation iterations
        batch_size: Batch size for parallel processing
        character: Character to simulate (Ironclad, Silent, Defect, Watcher)
    """
    
    def __init__(
        self,
        root_seed: int = 20260202,
        iterations: int = 10000,
        batch_size: int = 100,
        character: str = "Ironclad"
    ):
        """
        Initialize the Monte Carlo simulator.
        
        Args:
            root_seed: Root seed for deterministic RNG (default: 20260202)
            iterations: Number of iterations to run (default: 10000)
            batch_size: Batch size for processing (default: 100)
            character: Character to simulate (default: Ironclad)
        """
        self.root_seed = root_seed
        self.iterations = iterations
        self.batch_size = batch_size
        self.character = character
        self.runner = MonteCarloTestRunner()
    
    def run_base_scenario(self) -> Dict[str, Any]:
        """
        Run BASE scenario: deterministic behavior, no heuristics.
        
        Returns:
            Simulation results dictionary
        """
        scenario = create_base_scenario(
            root_seed=self.root_seed,
            iterations=self.iterations
        )
        result = self.runner.run_test_suite(self.character, scenario)
        return self._format_results(result, "BASE")
    
    def run_complex_scenario(self) -> Dict[str, Any]:
        """
        Run COMPLEX scenario: synergy-driven decision trees.
        
        Returns:
            Simulation results dictionary
        """
        scenario = create_complex_scenario(
            root_seed=self.root_seed,
            iterations=self.iterations
        )
        result = self.runner.run_test_suite(self.character, scenario)
        return self._format_results(result, "COMPLEX")
    
    def run_ideal_scenario(self) -> Dict[str, Any]:
        """
        Run IDEAL scenario: perfect-play oracle model.
        
        Returns:
            Simulation results dictionary
        """
        scenario = create_ideal_scenario(
            root_seed=self.root_seed,
            iterations=self.iterations
        )
        result = self.runner.run_test_suite(self.character, scenario)
        return self._format_results(result, "IDEAL")
    
    def run_random_scenario(self) -> Dict[str, Any]:
        """
        Run RANDOM scenario: stress-test for robustness.
        
        Returns:
            Simulation results dictionary
        """
        scenario = create_random_scenario(
            root_seed=self.root_seed,
            iterations=self.iterations
        )
        result = self.runner.run_test_suite(self.character, scenario)
        return self._format_results(result, "RANDOM")
    
    def run_all_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """
        Run all 4 scenario types.
        
        Returns:
            Dictionary mapping scenario names to results
        """
        return {
            "BASE": self.run_base_scenario(),
            "COMPLEX": self.run_complex_scenario(),
            "IDEAL": self.run_ideal_scenario(),
            "RANDOM": self.run_random_scenario(),
        }
    
    def run_scenario(self, scenario_type: str) -> Dict[str, Any]:
        """
        Run a specific scenario by name.
        
        Args:
            scenario_type: Scenario type (BASE, COMPLEX, IDEAL, RANDOM)
            
        Returns:
            Simulation results dictionary
            
        Raises:
            ValueError: If scenario_type is invalid
        """
        scenario_type = scenario_type.upper()
        
        if scenario_type == "BASE":
            return self.run_base_scenario()
        elif scenario_type == "COMPLEX":
            return self.run_complex_scenario()
        elif scenario_type == "IDEAL":
            return self.run_ideal_scenario()
        elif scenario_type == "RANDOM":
            return self.run_random_scenario()
        else:
            raise ValueError(f"Invalid scenario type: {scenario_type}")
    
    def _format_results(self, result: Any, scenario_name: str) -> Dict[str, Any]:
        """
        Format test suite results into a standard dictionary.
        
        Args:
            result: TestSuiteResult object
            scenario_name: Name of the scenario
            
        Returns:
            Formatted results dictionary
        """
        summary = result.summary_stats
        
        return {
            "scenario": scenario_name,
            "character": self.character,
            "iterations": self.iterations,
            "root_seed": self.root_seed,
            "win_rate": summary["win_rate"],
            "mean_turns": summary["mean_turns"],
            "median_turns": summary["median_turns"],
            "std_turns": summary["std_turns"],
            "min_turns": summary.get("min_turns", 0),
            "max_turns": summary.get("max_turns", 0),
            "total_runs": result.total_runs,
            "convergence_data": result.convergence_data,
        }
    
    def save_results(self, results: Dict[str, Any], output_path: Path):
        """
        Save simulation results to JSON file.
        
        Args:
            results: Results dictionary
            output_path: Path to save results
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
    
    @staticmethod
    def compare_scenarios(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare results across different scenarios.
        
        Args:
            results: Dictionary mapping scenario names to results
            
        Returns:
            Comparison summary
        """
        comparison = {
            "scenarios": list(results.keys()),
            "win_rates": {},
            "mean_turns": {},
            "best_scenario": None,
            "worst_scenario": None,
        }
        
        for scenario, result in results.items():
            comparison["win_rates"][scenario] = result["win_rate"]
            comparison["mean_turns"][scenario] = result["mean_turns"]
        
        # Find best and worst by win rate
        if comparison["win_rates"]:
            comparison["best_scenario"] = max(
                comparison["win_rates"],
                key=comparison["win_rates"].get
            )
            comparison["worst_scenario"] = min(
                comparison["win_rates"],
                key=comparison["win_rates"].get
            )
        
        return comparison


def run_simulation_batch(
    root_seed: int = 20260202,
    iterations: int = 10000,
    characters: Optional[List[str]] = None,
    scenarios: Optional[List[str]] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run a batch of simulations across multiple characters and scenarios.
    
    Args:
        root_seed: Root seed for reproducibility
        iterations: Number of iterations per scenario
        characters: List of characters to simulate (default: all)
        scenarios: List of scenarios to run (default: all)
        output_dir: Directory to save results (optional)
        
    Returns:
        Dictionary with all results
    """
    if characters is None:
        characters = ["Ironclad", "Silent", "Defect", "Watcher"]
    
    if scenarios is None:
        scenarios = ["BASE", "COMPLEX", "IDEAL", "RANDOM"]
    
    all_results = {}
    
    for character in characters:
        simulator = MonteCarloSimulator(
            root_seed=root_seed,
            iterations=iterations,
            character=character
        )
        
        character_results = {}
        for scenario in scenarios:
            print(f"Running {scenario} scenario for {character}...")
            result = simulator.run_scenario(scenario)
            character_results[scenario] = result
        
        all_results[character] = character_results
        
        if output_dir:
            output_path = output_dir / f"{character}_results.json"
            with open(output_path, 'w') as f:
                json.dump(character_results, f, indent=2)
    
    return all_results
