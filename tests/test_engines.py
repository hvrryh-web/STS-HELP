"""
Integration tests for character engines.
"""

import pytest
import numpy as np

from engine_common import CombatResult


class TestIroncladEngine:
    """Tests for Ironclad engine."""
    
    def test_simulate_run_returns_result(self):
        """simulate_run returns a CombatResult."""
        from ironclad_engine import simulate_run
        
        rng = np.random.default_rng(42)
        result = simulate_run(rng)
        
        assert isinstance(result, CombatResult)
    
    def test_deterministic_simulation(self):
        """Same seed produces same result."""
        from ironclad_engine import simulate_run
        
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        
        result1 = simulate_run(rng1)
        result2 = simulate_run(rng2)
        
        assert result1.win == result2.win
        assert result1.turns == result2.turns
        assert result1.damage_taken == result2.damage_taken
    
    def test_different_seeds_different_results(self):
        """Different seeds can produce different results."""
        from ironclad_engine import simulate_run
        
        results = []
        for seed in range(10):
            rng = np.random.default_rng(seed)
            results.append(simulate_run(rng))
        
        # Not all results should be identical
        wins = [r.win for r in results]
        assert not all(w == wins[0] for w in wins) or len(set([r.turns for r in results])) > 1


class TestSilentEngine:
    """Tests for Silent engine."""
    
    def test_simulate_run_returns_result(self):
        """simulate_run returns a CombatResult."""
        from silent_engine import simulate_run
        
        rng = np.random.default_rng(42)
        result = simulate_run(rng)
        
        assert isinstance(result, CombatResult)
    
    def test_poison_tracking(self):
        """Peak poison is tracked correctly."""
        from silent_engine import simulate_run
        
        rng = np.random.default_rng(42)
        result = simulate_run(rng)
        
        # Peak poison should be >= 0
        assert result.peak_poison >= 0


class TestDefectEngine:
    """Tests for Defect engine."""
    
    def test_simulate_run_returns_result(self):
        """simulate_run returns a CombatResult."""
        from defect_engine import simulate_run
        
        rng = np.random.default_rng(42)
        result = simulate_run(rng)
        
        assert isinstance(result, CombatResult)
    
    def test_orb_tracking(self):
        """Peak orbs is tracked correctly."""
        from defect_engine import simulate_run
        
        rng = np.random.default_rng(42)
        result = simulate_run(rng)
        
        # Peak orbs should be >= 0
        assert result.peak_orbs >= 0


class TestWatcherEngine:
    """Tests for Watcher engine."""
    
    def test_simulate_run_returns_result(self):
        """simulate_run returns a CombatResult."""
        from watcher_engine import simulate_run
        
        rng = np.random.default_rng(42)
        result = simulate_run(rng)
        
        assert isinstance(result, CombatResult)


class TestEngineConsistency:
    """Cross-engine consistency tests."""
    
    @pytest.mark.parametrize("character,engine_module", [
        ("Ironclad", "ironclad_engine"),
        ("Silent", "silent_engine"),
        ("Defect", "defect_engine"),
        ("Watcher", "watcher_engine"),
    ])
    def test_engine_runs_complete(self, character, engine_module):
        """All engines complete without errors."""
        import importlib
        engine = importlib.import_module(engine_module)
        
        rng = np.random.default_rng(42)
        result = engine.simulate_run(rng)
        
        assert isinstance(result, CombatResult)
        assert result.turns > 0
        assert result.cards_played >= 0
