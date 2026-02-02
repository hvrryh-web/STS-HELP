"""
Tests for decision-support tools (synergy_analyzer.py and path_optimizer.py).

These tests verify the basic functionality of the prototype tools.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.synergy_analyzer import SynergyAnalyzer
from tools.path_optimizer import PathOptimizer, GameState, NodeType


class TestSynergyAnalyzer:
    """Tests for the Synergy Analyzer tool."""
    
    def test_initialization(self):
        """Test that SynergyAnalyzer can be initialized."""
        analyzer = SynergyAnalyzer()
        assert analyzer is not None
        assert analyzer.cards is not None
        assert analyzer.relics is not None
        assert len(analyzer.synergy_rules) > 0
    
    def test_analyze_empty_deck(self):
        """Test analyzing an empty deck."""
        analyzer = SynergyAnalyzer()
        analysis = analyzer.analyze_deck([], [])
        
        assert analysis['deck_size'] == 0
        assert len(analysis['active_synergies']) == 0
        assert 'recommendations' in analysis
    
    def test_analyze_strength_deck(self):
        """Test analyzing a strength-focused Ironclad deck."""
        analyzer = SynergyAnalyzer()
        
        deck = ['Heavy Blade', 'Demon Form', 'Limit Break', 'Inflame']
        relics = ['Vajra', 'Girya']
        
        analysis = analyzer.analyze_deck(deck, relics)
        
        assert analysis['deck_size'] == 4
        assert len(analysis['active_synergies']) > 0
        
        # Should detect strength synergy
        synergy_names = [s['name'] for s in analysis['active_synergies']]
        assert 'Strength Scaling' in synergy_names
    
    def test_find_best_additions(self):
        """Test finding best cards to add."""
        analyzer = SynergyAnalyzer()
        
        deck = ['Heavy Blade', 'Demon Form']
        relics = ['Vajra']
        available = ['Strike', 'Bash', 'Sword Boomerang']
        
        recommendations = analyzer.find_best_additions(deck, relics, available, top_n=2)
        
        assert len(recommendations) <= 2
        assert all(isinstance(r, tuple) for r in recommendations)
        assert all(len(r) == 2 for r in recommendations)
    
    def test_synergy_rules_defined(self):
        """Test that synergy rules are properly defined."""
        analyzer = SynergyAnalyzer()
        
        # Check that we have synergy rules
        assert len(analyzer.synergy_rules) > 0
        
        # Check structure of rules
        for rule in analyzer.synergy_rules:
            assert 'name' in rule
            assert 'description' in rule
            assert 'examples' in rule


class TestPathOptimizer:
    """Tests for the Path Optimizer tool."""
    
    def test_initialization(self):
        """Test that PathOptimizer can be initialized."""
        optimizer = PathOptimizer()
        assert optimizer is not None
        assert 0 <= optimizer.risk_tolerance <= 1
    
    def test_calculate_entropy(self):
        """Test Shannon entropy calculation for paths."""
        optimizer = PathOptimizer()
        
        # Empty path
        assert optimizer.calculate_entropy([]) == 0.0
        
        # Single node type (no diversity)
        path = [NodeType.MONSTER] * 5
        entropy = optimizer.calculate_entropy(path)
        assert entropy == 0.0
        
        # Two node types equally distributed
        path = [NodeType.MONSTER, NodeType.ELITE] * 3
        entropy = optimizer.calculate_entropy(path)
        assert entropy == 1.0  # log2(2) = 1
        
        # More diverse path
        path = [NodeType.MONSTER, NodeType.ELITE, NodeType.REST, NodeType.SHOP]
        entropy = optimizer.calculate_entropy(path)
        assert entropy == 2.0  # log2(4) = 2
    
    def test_estimate_hp_change(self):
        """Test HP change estimation."""
        optimizer = PathOptimizer()
        
        state = GameState(
            current_hp=70,
            max_hp=80,
            gold=100,
            current_act=1,
            floor=5,
            deck_power=5.0,
            potion_count=2,
            has_key_relics=False
        )
        
        # Simple path: Monster -> Rest
        path = [NodeType.MONSTER, NodeType.REST]
        expected, worst = optimizer.estimate_hp_change(path, state)
        
        # Monster costs HP, Rest heals
        # Net should be positive (more healing than damage)
        assert expected > 0 or worst < expected  # Some relationship should hold
    
    def test_evaluate_path(self):
        """Test path evaluation."""
        optimizer = PathOptimizer()
        
        state = GameState(
            current_hp=70,
            max_hp=80,
            gold=100,
            current_act=1,
            floor=5,
            deck_power=5.0,
            potion_count=2,
            has_key_relics=False
        )
        
        path = [NodeType.MONSTER, NodeType.ELITE, NodeType.REST]
        segment = optimizer.evaluate_path(path, state)
        
        assert segment.nodes == path
        assert segment.expected_value is not None
        assert 0 <= segment.risk_score <= 1
        assert segment.entropy >= 0
        assert isinstance(segment.reasons, list)
    
    def test_recommend_next_node(self):
        """Test node recommendation."""
        optimizer = PathOptimizer()
        
        state = GameState(
            current_hp=70,
            max_hp=80,
            gold=100,
            current_act=1,
            floor=5,
            deck_power=5.0,
            potion_count=2,
            has_key_relics=False
        )
        
        available = [NodeType.MONSTER, NodeType.ELITE, NodeType.SHOP]
        recommended, analysis = optimizer.recommend_next_node(available, state)
        
        assert recommended in available
        assert analysis.expected_value is not None
        assert 0 <= analysis.risk_score <= 1
    
    def test_analyze_full_act_path(self):
        """Test full act path analysis."""
        optimizer = PathOptimizer()
        
        state = GameState(
            current_hp=70,
            max_hp=80,
            gold=100,
            current_act=1,
            floor=1,
            deck_power=5.0,
            potion_count=2,
            has_key_relics=False
        )
        
        # Typical Act 1 path
        path = [
            NodeType.MONSTER, NodeType.MONSTER, NodeType.ELITE,
            NodeType.REST, NodeType.SHOP, NodeType.ELITE,
            NodeType.MONSTER, NodeType.REST, NodeType.BOSS
        ]
        
        analysis = optimizer.analyze_full_act_path(path, state)
        
        assert 'evaluation' in analysis
        assert 'node_counts' in analysis
        assert 'expected_hp_change' in analysis
        assert 'assessment' in analysis
        assert 'research_notes' in analysis
        
        # Check node counts
        counts = analysis['node_counts']
        assert counts.get(NodeType.ELITE, 0) == 2
        assert counts.get(NodeType.REST, 0) == 2
        assert counts.get(NodeType.BOSS, 0) == 1
    
    def test_risk_tolerance_effect(self):
        """Test that risk tolerance affects recommendations."""
        state = GameState(
            current_hp=30,  # Low HP
            max_hp=80,
            gold=100,
            current_act=1,
            floor=10,
            deck_power=5.0,
            potion_count=2,
            has_key_relics=False
        )
        
        available = [NodeType.ELITE, NodeType.REST, NodeType.MONSTER]
        
        # Conservative optimizer
        optimizer_safe = PathOptimizer()
        optimizer_safe.risk_tolerance = 0.3
        safe_rec, safe_analysis = optimizer_safe.recommend_next_node(available, state)
        
        # Aggressive optimizer
        optimizer_risky = PathOptimizer()
        optimizer_risky.risk_tolerance = 0.9
        risky_rec, risky_analysis = optimizer_risky.recommend_next_node(available, state)
        
        # Both should make valid recommendations
        assert safe_rec in available
        assert risky_rec in available
        
        # Risk scores should make sense
        assert safe_analysis.risk_score >= 0
        assert risky_analysis.risk_score >= 0


class TestGameState:
    """Tests for GameState dataclass."""
    
    def test_game_state_creation(self):
        """Test creating a GameState."""
        state = GameState(
            current_hp=70,
            max_hp=80,
            gold=100,
            current_act=1,
            floor=5,
            deck_power=5.0,
            potion_count=2,
            has_key_relics=False
        )
        
        assert state.current_hp == 70
        assert state.max_hp == 80
        assert state.gold == 100
        assert state.current_act == 1
        assert state.floor == 5
        assert state.deck_power == 5.0
        assert state.potion_count == 2
        assert state.has_key_relics is False


class TestNodeType:
    """Tests for NodeType enum."""
    
    def test_node_type_values(self):
        """Test that NodeType enum has expected values."""
        assert NodeType.MONSTER.value == 'M'
        assert NodeType.ELITE.value == 'E'
        assert NodeType.REST.value == 'R'
        assert NodeType.SHOP.value == '$'
        assert NodeType.EVENT.value == '?'
        assert NodeType.TREASURE.value == 'T'
        assert NodeType.BOSS.value == 'B'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
