"""
Unit tests for src.simulation module.
"""

import pytest
from pathlib import Path
import tempfile

from src.simulation.simulator import MonteCarloSimulator, run_simulation_batch
from src.simulation.metrics import SimulationMetrics, calculate_metrics_from_results


class TestMonteCarloSimulator:
    """Tests for MonteCarloSimulator class."""
    
    def test_simulator_initialization(self):
        """Simulator can be initialized with parameters."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=100,
            character="Ironclad"
        )
        
        assert simulator.root_seed == 42
        assert simulator.iterations == 100
        assert simulator.character == "Ironclad"
    
    def test_run_base_scenario(self):
        """BASE scenario can be run."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,  # Small for testing
            character="Ironclad"
        )
        
        result = simulator.run_base_scenario()
        
        assert "scenario" in result
        assert result["scenario"] == "BASE"
        assert "win_rate" in result
        assert "mean_turns" in result
        assert result["iterations"] == 50
    
    def test_run_complex_scenario(self):
        """COMPLEX scenario can be run."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,
            character="Ironclad"
        )
        
        result = simulator.run_complex_scenario()
        
        assert result["scenario"] == "COMPLEX"
        assert "win_rate" in result
    
    def test_run_ideal_scenario(self):
        """IDEAL scenario can be run."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,
            character="Ironclad"
        )
        
        result = simulator.run_ideal_scenario()
        
        assert result["scenario"] == "IDEAL"
        assert "win_rate" in result
    
    def test_run_random_scenario(self):
        """RANDOM scenario can be run."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,
            character="Ironclad"
        )
        
        result = simulator.run_random_scenario()
        
        assert result["scenario"] == "RANDOM"
        assert "win_rate" in result
    
    def test_run_scenario_by_name(self):
        """Scenario can be run by name."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,
            character="Ironclad"
        )
        
        result = simulator.run_scenario("BASE")
        
        assert result["scenario"] == "BASE"
    
    def test_run_scenario_invalid_name(self):
        """Invalid scenario name raises ValueError."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,
            character="Ironclad"
        )
        
        with pytest.raises(ValueError):
            simulator.run_scenario("INVALID")
    
    def test_run_all_scenarios(self):
        """All scenarios can be run at once."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,
            character="Ironclad"
        )
        
        results = simulator.run_all_scenarios()
        
        assert "BASE" in results
        assert "COMPLEX" in results
        assert "IDEAL" in results
        assert "RANDOM" in results
    
    def test_compare_scenarios(self):
        """Scenarios can be compared."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,
            character="Ironclad"
        )
        
        results = simulator.run_all_scenarios()
        comparison = MonteCarloSimulator.compare_scenarios(results)
        
        assert "scenarios" in comparison
        assert "win_rates" in comparison
        assert "best_scenario" in comparison
        assert len(comparison["scenarios"]) == 4
    
    def test_save_results(self):
        """Results can be saved to file."""
        simulator = MonteCarloSimulator(
            root_seed=42,
            iterations=50,
            character="Ironclad"
        )
        
        result = simulator.run_base_scenario()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            simulator.save_results(result, output_path)
            
            assert output_path.exists()
    
    def test_deterministic_results(self):
        """Same seed produces same results."""
        sim1 = MonteCarloSimulator(root_seed=123, iterations=50, character="Ironclad")
        sim2 = MonteCarloSimulator(root_seed=123, iterations=50, character="Ironclad")
        
        result1 = sim1.run_base_scenario()
        result2 = sim2.run_base_scenario()
        
        # Results should be identical with same seed
        assert result1["win_rate"] == result2["win_rate"]
        assert result1["mean_turns"] == result2["mean_turns"]


class TestSimulationMetrics:
    """Tests for SimulationMetrics class."""
    
    def test_metrics_initialization(self):
        """Metrics can be initialized with results."""
        results = [
            {"won": True, "turns_taken": 10, "player_hp": 50, "total_damage_dealt": 200},
            {"won": False, "turns_taken": 15, "player_hp": 0, "total_damage_dealt": 150},
        ]
        
        metrics = SimulationMetrics(results)
        
        assert len(metrics.results) == 2
        assert len(metrics.wins) == 2
        assert len(metrics.turns) == 2
    
    def test_calculate_win_rate(self):
        """Win rate is calculated correctly."""
        results = [
            {"won": True, "turns_taken": 10, "player_hp": 50, "total_damage_dealt": 200},
            {"won": True, "turns_taken": 12, "player_hp": 40, "total_damage_dealt": 180},
            {"won": False, "turns_taken": 15, "player_hp": 0, "total_damage_dealt": 150},
        ]
        
        metrics = SimulationMetrics(results)
        win_rate = metrics.calculate_win_rate()
        
        assert win_rate == pytest.approx(66.67, abs=0.1)  # 2/3 = 66.67%
    
    def test_calculate_median_turns(self):
        """Median turns is calculated correctly."""
        results = [
            {"won": True, "turns_taken": 10, "player_hp": 50, "total_damage_dealt": 200},
            {"won": True, "turns_taken": 12, "player_hp": 40, "total_damage_dealt": 180},
            {"won": False, "turns_taken": 15, "player_hp": 0, "total_damage_dealt": 150},
        ]
        
        metrics = SimulationMetrics(results)
        median = metrics.calculate_median_turns()
        
        assert median == 12.0
    
    def test_calculate_variance(self):
        """Variance is calculated correctly."""
        results = [
            {"won": True, "turns_taken": 10, "player_hp": 50, "total_damage_dealt": 200},
            {"won": True, "turns_taken": 12, "player_hp": 40, "total_damage_dealt": 180},
            {"won": False, "turns_taken": 14, "player_hp": 0, "total_damage_dealt": 150},
        ]
        
        metrics = SimulationMetrics(results)
        variance = metrics.calculate_variance()
        
        assert variance > 0  # Should have some variance
    
    def test_calculate_tail_risk(self):
        """Tail risk is calculated correctly."""
        results = [
            {"won": True, "turns_taken": i, "player_hp": 50, "total_damage_dealt": 200}
            for i in range(1, 21)
        ]
        
        metrics = SimulationMetrics(results)
        tail_risk = metrics.calculate_tail_risk(5.0)
        
        assert "percentile" in tail_risk
        assert "threshold_turns" in tail_risk
        assert "failure_rate_in_tail" in tail_risk
        assert tail_risk["percentile"] == 5.0
    
    def test_get_all_metrics(self):
        """All metrics are returned in dictionary."""
        results = [
            {"won": True, "turns_taken": 10, "player_hp": 50, "total_damage_dealt": 200},
            {"won": False, "turns_taken": 15, "player_hp": 0, "total_damage_dealt": 150},
        ]
        
        metrics = SimulationMetrics(results)
        all_metrics = metrics.get_all_metrics()
        
        assert "win_rate" in all_metrics
        assert "median_turns" in all_metrics
        assert "variance" in all_metrics
        assert "tail_risk_5pct" in all_metrics
        assert "total_runs" in all_metrics
        assert all_metrics["total_runs"] == 2
    
    def test_get_percentiles(self):
        """Percentiles are calculated correctly."""
        results = [
            {"won": True, "turns_taken": i, "player_hp": 50, "total_damage_dealt": 200}
            for i in range(1, 101)
        ]
        
        metrics = SimulationMetrics(results)
        percentiles = metrics.get_percentiles([25, 50, 75])
        
        assert "p25" in percentiles
        assert "p50" in percentiles
        assert "p75" in percentiles
        assert percentiles["p50"] == pytest.approx(50.5, abs=1)
    
    def test_get_confidence_interval(self):
        """Confidence interval is calculated."""
        results = [
            {"won": True, "turns_taken": 10, "player_hp": 50, "total_damage_dealt": 200}
            for _ in range(60)
        ] + [
            {"won": False, "turns_taken": 15, "player_hp": 0, "total_damage_dealt": 150}
            for _ in range(40)
        ]
        
        metrics = SimulationMetrics(results)
        ci = metrics.get_confidence_interval(0.95)
        
        assert len(ci) == 2
        assert ci[0] < ci[1]  # Lower bound < upper bound
        assert 0 <= ci[0] <= 100
        assert 0 <= ci[1] <= 100


class TestRunSimulationBatch:
    """Tests for run_simulation_batch function."""
    
    def test_run_batch_single_character(self):
        """Batch can run for single character."""
        results = run_simulation_batch(
            root_seed=42,
            iterations=50,
            characters=["Ironclad"],
            scenarios=["BASE"]
        )
        
        assert "Ironclad" in results
        assert "BASE" in results["Ironclad"]
    
    def test_run_batch_multiple_scenarios(self):
        """Batch can run multiple scenarios."""
        results = run_simulation_batch(
            root_seed=42,
            iterations=50,
            characters=["Ironclad"],
            scenarios=["BASE", "COMPLEX"]
        )
        
        assert "BASE" in results["Ironclad"]
        assert "COMPLEX" in results["Ironclad"]
