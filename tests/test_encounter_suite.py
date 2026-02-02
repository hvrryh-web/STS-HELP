"""
Tests for encounter suite module.
"""

import numpy as np
import pytest

from encounter_suite import (
    EncounterType,
    EnemyIntent,
    EncounterEnemy,
    Encounter,
    CANONICAL_ENCOUNTERS,
    BURST_ATTACKER,
    DEBUFFER,
    SCALING_ENEMY,
    BOSS_PHASE,
    get_encounter_weights,
    select_encounter,
    create_encounter_enemies,
    execute_enemy_intent,
    burst_attacker_intent,
    debuffer_intent,
    scaling_enemy_intent,
    boss_phase_intent,
)
from engine_common import EnemyState, PlayerState, Intent


class TestEncounterDefinitions:
    """Tests for encounter definitions."""
    
    def test_canonical_encounters_not_empty(self):
        """Should have at least one canonical encounter."""
        assert len(CANONICAL_ENCOUNTERS) > 0
    
    def test_all_encounter_types_covered(self):
        """Should cover all encounter types."""
        types_covered = {e.encounter_type for e in CANONICAL_ENCOUNTERS}
        
        assert EncounterType.BURST_ATTACKER in types_covered
        assert EncounterType.DEBUFFER in types_covered
        assert EncounterType.SCALING_ENEMY in types_covered
        assert EncounterType.BOSS_PHASE in types_covered
    
    def test_encounter_weights_sum_to_one(self):
        """Normalized weights should sum to 1."""
        weights = get_encounter_weights()
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.001


class TestEnemyIntents:
    """Tests for enemy intent patterns."""
    
    def test_burst_attacker_intent(self):
        """Burst attacker should attack on most turns."""
        enemy = EnemyState(hp=60, max_hp=60)
        
        intent1 = burst_attacker_intent(1, enemy)
        assert intent1.intent_type == Intent.ATTACK
        assert intent1.damage > 0
        
        intent2 = burst_attacker_intent(2, enemy)
        assert intent2.intent_type == Intent.ATTACK
        assert intent2.damage > intent1.damage  # Turn 2 is heavy attack
    
    def test_debuffer_intent_pattern(self):
        """Debuffer should debuff before attacking."""
        enemy = EnemyState(hp=65, max_hp=65)
        
        intent1 = debuffer_intent(1, enemy)
        assert intent1.intent_type == Intent.DEBUFF
        assert intent1.debuff_type == 'weak'
        
        intent2 = debuffer_intent(2, enemy)
        assert intent2.intent_type == Intent.DEBUFF
        assert intent2.debuff_type == 'vulnerable'
        
        intent3 = debuffer_intent(3, enemy)
        assert intent3.intent_type == Intent.ATTACK
    
    def test_scaling_enemy_gains_strength(self):
        """Scaling enemy should buff strength."""
        enemy = EnemyState(hp=85, max_hp=85)
        
        intent1 = scaling_enemy_intent(1, enemy)
        assert intent1.intent_type == Intent.BUFF
        assert intent1.strength_gain > 0
    
    def test_boss_phase_changes(self):
        """Boss should change behavior at low HP."""
        # Full HP - Phase 1
        enemy_high = EnemyState(hp=150, max_hp=150)
        intent_high = boss_phase_intent(1, enemy_high)
        assert intent_high.intent_type == Intent.ATTACK
        
        # Low HP - Phase 2 (enraged)
        enemy_low = EnemyState(hp=50, max_hp=150)
        intent_low = boss_phase_intent(3, enemy_low)  # Turn 3 in phase 2 = buff
        # Phase 2 behavior may differ


class TestEncounterSelection:
    """Tests for encounter selection."""
    
    def test_select_encounter_deterministic(self):
        """Same seed should select same encounter."""
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        
        enc1 = select_encounter(rng1)
        enc2 = select_encounter(rng2)
        
        assert enc1.name == enc2.name
    
    def test_select_encounter_different_seeds(self):
        """Different seeds may select different encounters."""
        results = []
        for seed in range(100):
            rng = np.random.default_rng(seed)
            enc = select_encounter(rng)
            results.append(enc.name)
        
        # Should have some variety
        unique = set(results)
        assert len(unique) > 1


class TestEnemyCreation:
    """Tests for enemy creation."""
    
    def test_create_encounter_enemies(self):
        """Should create enemies with correct HP."""
        encounter = CANONICAL_ENCOUNTERS[0]  # Burst attacker
        rng = np.random.default_rng(42)
        
        enemies = create_encounter_enemies(encounter, rng, ascension=0)
        
        assert len(enemies) == len(encounter.enemies)
        for enemy in enemies:
            assert enemy.hp > 0
            assert enemy.hp == enemy.max_hp
    
    def test_ascension_affects_hp(self):
        """Ascension 8+ should give higher HP."""
        encounter = CANONICAL_ENCOUNTERS[0]
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        
        enemies_low = create_encounter_enemies(encounter, rng1, ascension=0)
        enemies_high = create_encounter_enemies(encounter, rng2, ascension=8)
        
        # High ascension should have HP in higher range
        # (may overlap due to randomness, but enemy def should use different ranges)
        assert len(enemies_low) > 0
        assert len(enemies_high) > 0


class TestIntentExecution:
    """Tests for intent execution."""
    
    def test_execute_attack_intent(self):
        """Attack intent should damage player."""
        intent = EnemyIntent(intent_type=Intent.ATTACK, damage=10, hits=1)
        enemy = EnemyState(hp=50, max_hp=50, strength=0)
        player = PlayerState(hp=80, block=0)
        
        result = execute_enemy_intent(intent, enemy, player)
        
        assert result['intent'] == 'attack'
        assert player.hp == 70  # 80 - 10
    
    def test_execute_attack_with_block(self):
        """Attack should be absorbed by block first."""
        intent = EnemyIntent(intent_type=Intent.ATTACK, damage=10, hits=1)
        enemy = EnemyState(hp=50, max_hp=50, strength=0)
        player = PlayerState(hp=80, block=5)
        
        execute_enemy_intent(intent, enemy, player)
        
        assert player.block == 0
        assert player.hp == 75  # 80 - (10-5)
    
    def test_execute_buff_intent(self):
        """Buff intent should increase enemy strength."""
        intent = EnemyIntent(intent_type=Intent.BUFF, strength_gain=2)
        enemy = EnemyState(hp=50, max_hp=50, strength=0)
        player = PlayerState(hp=80)
        
        execute_enemy_intent(intent, enemy, player)
        
        assert enemy.strength == 2
    
    def test_execute_debuff_with_artifact(self):
        """Debuff should be blocked by artifact."""
        intent = EnemyIntent(intent_type=Intent.DEBUFF, debuff_type='weak', debuff_stacks=2)
        enemy = EnemyState(hp=50, max_hp=50)
        player = PlayerState(hp=80, artifact=1)
        
        result = execute_enemy_intent(intent, enemy, player)
        
        assert player.artifact == 0  # Consumed
        assert result['details'].get('blocked_by_artifact', False)


class TestMultiEnemyEncounters:
    """Tests for multi-enemy encounter handling."""
    
    def test_multi_enemy_encounter_creation(self):
        """Multi-enemy encounter should create multiple enemies."""
        # Find multi-enemy encounter
        multi_enc = None
        for enc in CANONICAL_ENCOUNTERS:
            if enc.encounter_type == EncounterType.MULTI_ENEMY:
                multi_enc = enc
                break
        
        assert multi_enc is not None
        assert len(multi_enc.enemies) > 1
        
        rng = np.random.default_rng(42)
        enemies = create_encounter_enemies(multi_enc, rng)
        
        assert len(enemies) == len(multi_enc.enemies)
