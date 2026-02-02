"""
Tests for simulation configuration module.

Verifies that all heuristics and configurations are properly documented
and can be serialized/deserialized for reproducibility.
"""

import json
import pytest

from simulation_config import (
    SimulationConfig,
    CardValueHeuristics,
    EnemyBehaviorHeuristics,
    ScoringHeuristics,
    ScenarioType,
    EnemyProfile,
    DifficultyTier,
    get_baseline_config,
    get_calibration_config,
    get_stress_test_config,
    get_quick_test_config,
    get_data_gaps,
    get_assumptions,
    get_documentation_report,
    DATA_GAPS,
    ASSUMPTIONS,
)


class TestCardValueHeuristics:
    """Tests for card value heuristics."""
    
    def test_default_values(self):
        """Verify default values are set correctly."""
        h = CardValueHeuristics()
        
        assert h.damage_per_hp == 1.0
        assert h.vulnerable_multiplier == 1.5
        assert h.block_when_threatened == 1.2
        assert h.draw_value == 4.0
    
    def test_to_dict(self):
        """Verify serialization to dict."""
        h = CardValueHeuristics()
        d = h.to_dict()
        
        assert isinstance(d, dict)
        assert 'damage_per_hp' in d
        assert 'vulnerable_multiplier' in d
        assert 'apply_energy_efficiency' in d
    
    def test_custom_values(self):
        """Verify custom values can be set."""
        h = CardValueHeuristics(
            damage_per_hp=1.5,
            vulnerable_multiplier=2.0,
            draw_value=5.0,
        )
        
        assert h.damage_per_hp == 1.5
        assert h.vulnerable_multiplier == 2.0
        assert h.draw_value == 5.0


class TestEnemyBehaviorHeuristics:
    """Tests for enemy behavior heuristics."""
    
    def test_default_values(self):
        """Verify default values are set correctly."""
        h = EnemyBehaviorHeuristics()
        
        assert h.attack_probability_early == 0.7
        assert h.base_damage_turn1 == 18
        assert h.strength_per_buff == 3
    
    def test_to_dict(self):
        """Verify serialization to dict."""
        h = EnemyBehaviorHeuristics()
        d = h.to_dict()
        
        assert isinstance(d, dict)
        assert 'attack_probability_early' in d
        assert 'base_damage_normal' in d
    
    def test_custom_values(self):
        """Verify custom values for stress testing."""
        h = EnemyBehaviorHeuristics(
            base_damage_turn1=25,
            damage_scaling_per_turn=5,
        )
        
        assert h.base_damage_turn1 == 25
        assert h.damage_scaling_per_turn == 5


class TestScoringHeuristics:
    """Tests for scoring heuristics."""
    
    def test_default_values(self):
        """Verify default values are set correctly."""
        h = ScoringHeuristics()
        
        assert h.baseline_prediction == 50.0
        assert h.apv_lambda == 0.3
        assert h.cgv_beta == 0.1
        assert h.win_reward == 100
    
    def test_to_dict(self):
        """Verify serialization to dict."""
        h = ScoringHeuristics()
        d = h.to_dict()
        
        assert isinstance(d, dict)
        assert 'baseline_prediction' in d
        assert 'greed_percentile' in d


class TestSimulationConfig:
    """Tests for main simulation configuration."""
    
    def test_default_config(self):
        """Verify default configuration."""
        config = SimulationConfig()
        
        assert config.root_seed == 42
        assert config.runs_per_batch == 1000
        assert config.enemy_hp == 120
        assert config.scenario_type == ScenarioType.BASELINE
    
    def test_to_dict(self):
        """Verify configuration serialization."""
        config = SimulationConfig()
        d = config.to_dict()
        
        assert isinstance(d, dict)
        assert 'root_seed' in d
        assert 'card_heuristics' in d
        assert 'enemy_heuristics' in d
        assert 'scoring_heuristics' in d
        
        # Verify nested heuristics are serialized
        assert isinstance(d['card_heuristics'], dict)
        assert isinstance(d['enemy_heuristics'], dict)
        assert isinstance(d['scoring_heuristics'], dict)
    
    def test_json_serializable(self):
        """Verify configuration is JSON serializable."""
        config = SimulationConfig()
        d = config.to_dict()
        
        # Should not raise
        json_str = json.dumps(d)
        assert len(json_str) > 0
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed['root_seed'] == 42
    
    def test_from_dict(self):
        """Verify configuration deserialization."""
        original = SimulationConfig(
            root_seed=123,
            runs_per_batch=500,
            scenario_type=ScenarioType.UPGRADED_DECK,
        )
        
        d = original.to_dict()
        restored = SimulationConfig.from_dict(d)
        
        assert restored.root_seed == 123
        assert restored.runs_per_batch == 500
        assert restored.scenario_type == ScenarioType.UPGRADED_DECK
    
    def test_config_hash_deterministic(self):
        """Verify configuration hash is deterministic."""
        config1 = SimulationConfig(root_seed=42)
        config2 = SimulationConfig(root_seed=42)
        
        assert config1.get_config_hash() == config2.get_config_hash()
    
    def test_config_hash_different_for_different_config(self):
        """Verify different configurations have different hashes."""
        config1 = SimulationConfig(root_seed=42)
        config2 = SimulationConfig(root_seed=123)
        
        assert config1.get_config_hash() != config2.get_config_hash()
    
    def test_custom_heuristics(self):
        """Verify custom heuristics can be provided."""
        custom_card = CardValueHeuristics(damage_per_hp=2.0)
        custom_enemy = EnemyBehaviorHeuristics(base_damage_turn1=25)
        
        config = SimulationConfig(
            card_heuristics=custom_card,
            enemy_heuristics=custom_enemy,
        )
        
        assert config.card_heuristics.damage_per_hp == 2.0
        assert config.enemy_heuristics.base_damage_turn1 == 25


class TestScenarioPresets:
    """Tests for scenario preset configurations."""
    
    def test_baseline_config(self):
        """Verify baseline configuration preset."""
        config = get_baseline_config(seed=123, runs=500)
        
        assert config.root_seed == 123
        assert config.runs_per_batch == 500
        assert config.scenario_type == ScenarioType.BASELINE
        assert config.difficulty_tier == DifficultyTier.ELITE
    
    def test_calibration_config(self):
        """Verify calibration configuration preset."""
        config = get_calibration_config(seed=42)
        
        assert config.runs_per_batch == 5000
        assert config.batch_count == 4
        assert config.convergence_threshold == 0.01
    
    def test_stress_test_config(self):
        """Verify stress test configuration preset."""
        config = get_stress_test_config()
        
        assert config.enemy_hp == 150
        assert config.difficulty_tier == DifficultyTier.BOSS
        assert config.enemy_heuristics.base_damage_turn1 == 25
    
    def test_quick_test_config(self):
        """Verify quick test configuration preset."""
        config = get_quick_test_config()
        
        assert config.runs_per_batch == 100
        assert config.generate_charts is False
        assert config.generate_pdf_report is False


class TestEnums:
    """Tests for enumeration types."""
    
    def test_scenario_types(self):
        """Verify all scenario types are defined."""
        assert ScenarioType.BASELINE.value == "baseline"
        assert ScenarioType.UPGRADED_DECK.value == "upgraded"
        assert ScenarioType.BOSS_FIGHT.value == "boss"
    
    def test_enemy_profiles(self):
        """Verify all enemy profiles are defined."""
        assert EnemyProfile.BURST_ATTACKER.value == "burst"
        assert EnemyProfile.DEBUFFER.value == "debuffer"
        assert EnemyProfile.SCALING_THREAT.value == "scaling"
    
    def test_difficulty_tiers(self):
        """Verify all difficulty tiers are defined."""
        assert DifficultyTier.EASY.value == "easy"
        assert DifficultyTier.ELITE.value == "elite"
        assert DifficultyTier.BOSS.value == "boss"


class TestDocumentation:
    """Tests for documentation and data gap tracking."""
    
    def test_data_gaps_structure(self):
        """Verify data gaps are properly structured."""
        gaps = get_data_gaps()
        
        assert len(gaps) > 0
        
        for gap in gaps:
            assert 'id' in gap
            assert 'category' in gap
            assert 'description' in gap
            assert 'impact' in gap
            assert 'mitigation' in gap
    
    def test_assumptions_structure(self):
        """Verify assumptions are properly structured."""
        assumptions = get_assumptions()
        
        assert len(assumptions) > 0
        
        for assumption in assumptions:
            assert 'id' in assumption
            assert 'category' in assumption
            assert 'assumption' in assumption
            assert 'justification' in assumption
    
    def test_documentation_report(self):
        """Verify documentation report is complete."""
        report = get_documentation_report()
        
        assert 'version' in report
        assert 'heuristics' in report
        assert 'assumptions' in report
        assert 'data_gaps' in report
        assert 'scenario_types' in report
        assert 'enemy_profiles' in report
        assert 'difficulty_tiers' in report
        
        # Verify heuristics are included
        assert 'card_value' in report['heuristics']
        assert 'enemy_behavior' in report['heuristics']
        assert 'scoring' in report['heuristics']
    
    def test_documentation_report_json_serializable(self):
        """Verify documentation report is JSON serializable."""
        report = get_documentation_report()
        
        # Should not raise
        json_str = json.dumps(report)
        assert len(json_str) > 0
    
    def test_data_gaps_have_unique_ids(self):
        """Verify data gap IDs are unique."""
        gaps = get_data_gaps()
        ids = [g['id'] for g in gaps]
        
        assert len(ids) == len(set(ids)), "Data gap IDs should be unique"
    
    def test_assumptions_have_unique_ids(self):
        """Verify assumption IDs are unique."""
        assumptions = get_assumptions()
        ids = [a['id'] for a in assumptions]
        
        assert len(ids) == len(set(ids)), "Assumption IDs should be unique"
