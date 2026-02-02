"""
Canonical enemy encounter suite for calibration.

As recommended in critical review Section 2.4:
- Burst attacker: High damage, low HP
- Debuffer: Applies debuffs before attacking
- Scaling enemy: Gains strength/damage over time
- Multi-enemy: Multiple targets
- Boss-like: Phase switching behavior

This provides a more stable calibration surface than a single elite proxy.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Callable, Optional, Tuple
import numpy as np

from engine_common import EnemyState, Intent, PlayerState


class EncounterType(Enum):
    """Types of canonical encounters."""
    BURST_ATTACKER = "burst_attacker"
    DEBUFFER = "debuffer"
    SCALING_ENEMY = "scaling_enemy"
    MULTI_ENEMY = "multi_enemy"
    BOSS_PHASE = "boss_phase"


@dataclass
class EnemyIntent:
    """Detailed enemy intent with action specifics."""
    intent_type: Intent
    damage: int = 0
    hits: int = 1
    block: int = 0
    strength_gain: int = 0
    debuff_type: str = ""
    debuff_stacks: int = 0


@dataclass
class EncounterEnemy:
    """
    Enemy definition for encounter suite.
    
    Attributes:
        name: Enemy name.
        base_hp: Base HP range (min, max).
        ascension_hp: Ascension 8+ HP range.
        intent_pattern: Function that returns next intent.
        passive: Optional passive effect description.
    """
    name: str
    base_hp: Tuple[int, int]
    ascension_hp: Tuple[int, int]
    get_intent: Callable[[int, 'EnemyState'], EnemyIntent]
    passive: str = ""


@dataclass
class Encounter:
    """
    An encounter consisting of one or more enemies.
    
    Attributes:
        name: Encounter name.
        encounter_type: Type classification.
        enemies: List of enemies in encounter.
        weight: Relative weight for encounter selection (default 1.0).
        act: Which act this encounter represents (1, 2, 3).
    """
    name: str
    encounter_type: EncounterType
    enemies: List[EncounterEnemy]
    weight: float = 1.0
    act: int = 1


# ============================================================================
# BURST ATTACKER: High damage, lower HP, attacks aggressively
# ============================================================================

def burst_attacker_intent(turn: int, enemy: EnemyState) -> EnemyIntent:
    """
    Burst attacker pattern: Heavy attacks with occasional big hits.
    
    Pattern:
    - Turn 1: Medium attack (12 damage)
    - Turn 2: Heavy attack (20 damage)
    - Turn 3+: Cycle medium/heavy
    """
    if turn % 3 == 1:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=12, hits=1)
    elif turn % 3 == 2:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=20, hits=1)
    else:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=8, hits=2)


BURST_ATTACKER = EncounterEnemy(
    name="Marauder",
    base_hp=(55, 65),
    ascension_hp=(60, 70),
    get_intent=burst_attacker_intent,
    passive="Attacks aggressively with high damage"
)


# ============================================================================
# DEBUFFER: Applies debuffs before attacking
# ============================================================================

def debuffer_intent(turn: int, enemy: EnemyState) -> EnemyIntent:
    """
    Debuffer pattern: Weakens player before dealing damage.
    
    Pattern:
    - Turn 1: Apply Weak (2 stacks)
    - Turn 2: Apply Vulnerable (2 stacks)
    - Turn 3: Attack (15 damage)
    - Turn 4+: Cycle
    """
    cycle = turn % 4
    if cycle == 1:
        return EnemyIntent(
            intent_type=Intent.DEBUFF, 
            debuff_type="weak", 
            debuff_stacks=2
        )
    elif cycle == 2:
        return EnemyIntent(
            intent_type=Intent.DEBUFF, 
            debuff_type="vulnerable", 
            debuff_stacks=2
        )
    elif cycle == 3:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=15, hits=1)
    else:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=10, hits=1)


DEBUFFER = EncounterEnemy(
    name="Hexcaster",
    base_hp=(60, 70),
    ascension_hp=(65, 75),
    get_intent=debuffer_intent,
    passive="Alternates between debuffs and attacks"
)


# ============================================================================
# SCALING ENEMY: Gains strength over time (like Nob pattern)
# ============================================================================

def scaling_enemy_intent(turn: int, enemy: EnemyState) -> EnemyIntent:
    """
    Scaling enemy pattern: Buffs self then attacks with increasing damage.
    
    Pattern:
    - Turn 1: Gain 2 Strength (buff phase)
    - Turn 2: Attack (10 + strength)
    - Turn 3: Gain 2 Strength
    - Turn 4+: Attack/Buff cycle
    
    The enemy's base attack is 10, but strength from buffs adds to this.
    """
    if turn == 1 or turn % 3 == 0:
        return EnemyIntent(
            intent_type=Intent.BUFF, 
            strength_gain=2
        )
    else:
        # Base damage 10, actual damage includes enemy strength
        return EnemyIntent(intent_type=Intent.ATTACK, damage=10, hits=1)


SCALING_ENEMY = EncounterEnemy(
    name="Warlord",
    base_hp=(80, 90),
    ascension_hp=(85, 95),
    get_intent=scaling_enemy_intent,
    passive="Gains 2 Strength periodically"
)


# ============================================================================
# MULTI-ENEMY: Multiple targets that coordinate
# ============================================================================

def multi_enemy_front_intent(turn: int, enemy: EnemyState) -> EnemyIntent:
    """Front enemy in multi-enemy: Attacks and sometimes blocks."""
    if turn % 3 == 1:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=8, hits=1)
    elif turn % 3 == 2:
        return EnemyIntent(intent_type=Intent.DEFEND, block=10)
    else:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=12, hits=1)


def multi_enemy_back_intent(turn: int, enemy: EnemyState) -> EnemyIntent:
    """Back enemy in multi-enemy: Ranged attacks and status."""
    if turn % 3 == 1:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=6, hits=2)
    elif turn % 3 == 2:
        return EnemyIntent(
            intent_type=Intent.DEBUFF, 
            debuff_type="frail", 
            debuff_stacks=1
        )
    else:
        return EnemyIntent(intent_type=Intent.ATTACK, damage=10, hits=1)


MULTI_ENEMY_FRONT = EncounterEnemy(
    name="Guardian Sentry",
    base_hp=(35, 40),
    ascension_hp=(40, 45),
    get_intent=multi_enemy_front_intent,
    passive="Tank - attacks and blocks"
)

MULTI_ENEMY_BACK = EncounterEnemy(
    name="Ranged Sentry",
    base_hp=(30, 35),
    ascension_hp=(35, 40),
    get_intent=multi_enemy_back_intent,
    passive="Ranged - multi-hit and debuffs"
)


# ============================================================================
# BOSS-LIKE: Phase switching behavior
# ============================================================================

def boss_phase_intent(turn: int, enemy: EnemyState) -> EnemyIntent:
    """
    Boss-like pattern with phases.
    
    Phase 1 (HP > 50%): Standard attacks
    Phase 2 (HP <= 50%): Enraged - stronger attacks, gains strength
    
    Pattern (Phase 1):
    - Alternates between attack (14) and multi-attack (5x3)
    
    Pattern (Phase 2):
    - Turn after entering: Enrage (gain 3 strength)
    - Heavy attack (20)
    - Multi-attack (7x3)
    """
    # Determine phase based on HP percentage
    hp_percent = enemy.hp / enemy.max_hp if enemy.max_hp > 0 else 1.0
    
    if hp_percent > 0.5:
        # Phase 1: Standard attacks
        if turn % 2 == 1:
            return EnemyIntent(intent_type=Intent.ATTACK, damage=14, hits=1)
        else:
            return EnemyIntent(intent_type=Intent.ATTACK, damage=5, hits=3)
    else:
        # Phase 2: Enraged
        cycle = turn % 3
        if cycle == 0:
            return EnemyIntent(intent_type=Intent.BUFF, strength_gain=3)
        elif cycle == 1:
            return EnemyIntent(intent_type=Intent.ATTACK, damage=20, hits=1)
        else:
            return EnemyIntent(intent_type=Intent.ATTACK, damage=7, hits=3)


BOSS_PHASE = EncounterEnemy(
    name="Corrupted Champion",
    base_hp=(140, 150),
    ascension_hp=(150, 160),
    get_intent=boss_phase_intent,
    passive="Enters enraged state at 50% HP - gains strength and attacks harder"
)


# ============================================================================
# CANONICAL ENCOUNTER SUITE
# ============================================================================

CANONICAL_ENCOUNTERS = [
    Encounter(
        name="Burst Attack Test",
        encounter_type=EncounterType.BURST_ATTACKER,
        enemies=[BURST_ATTACKER],
        weight=1.0,
        act=1
    ),
    Encounter(
        name="Debuff Gauntlet",
        encounter_type=EncounterType.DEBUFFER,
        enemies=[DEBUFFER],
        weight=1.0,
        act=1
    ),
    Encounter(
        name="Strength Scaling Test",
        encounter_type=EncounterType.SCALING_ENEMY,
        enemies=[SCALING_ENEMY],
        weight=1.0,
        act=1
    ),
    Encounter(
        name="Multi-Target Combat",
        encounter_type=EncounterType.MULTI_ENEMY,
        enemies=[MULTI_ENEMY_FRONT, MULTI_ENEMY_BACK],
        weight=1.2,  # Slightly higher weight - important calibration
        act=1
    ),
    Encounter(
        name="Boss Phase Test",
        encounter_type=EncounterType.BOSS_PHASE,
        enemies=[BOSS_PHASE],
        weight=1.5,  # Boss encounters weighted higher
        act=1
    ),
]


def get_encounter_weights() -> Dict[str, float]:
    """Get normalized weights for encounter selection."""
    total_weight = sum(e.weight for e in CANONICAL_ENCOUNTERS)
    return {e.name: e.weight / total_weight for e in CANONICAL_ENCOUNTERS}


def select_encounter(rng: np.random.Generator) -> Encounter:
    """
    Select an encounter based on weights.
    
    Args:
        rng: Random number generator.
    
    Returns:
        Selected encounter.
    """
    weights = [e.weight for e in CANONICAL_ENCOUNTERS]
    total = sum(weights)
    probs = [w / total for w in weights]
    
    idx = rng.choice(len(CANONICAL_ENCOUNTERS), p=probs)
    return CANONICAL_ENCOUNTERS[idx]


def create_encounter_enemies(
    encounter: Encounter,
    rng: np.random.Generator,
    ascension: int = 0
) -> List[EnemyState]:
    """
    Create EnemyState instances for an encounter.
    
    Args:
        encounter: Encounter definition.
        rng: Random number generator.
        ascension: Ascension level (8+ uses higher HP).
    
    Returns:
        List of EnemyState instances.
    """
    enemies = []
    
    for enemy_def in encounter.enemies:
        # Select HP range based on ascension
        if ascension >= 8:
            hp_min, hp_max = enemy_def.ascension_hp
        else:
            hp_min, hp_max = enemy_def.base_hp
        
        hp = rng.integers(hp_min, hp_max + 1)
        
        enemy = EnemyState(
            hp=hp,
            max_hp=hp,
            block=0,
            strength=0,
            poison=0,
            vulnerable=0,
            weak=0,
            artifact=0
        )
        enemies.append(enemy)
    
    return enemies


def execute_enemy_intent(
    intent: EnemyIntent,
    enemy: EnemyState,
    player: PlayerState
) -> Dict[str, any]:
    """
    Execute an enemy's intent.
    
    Args:
        intent: Intent to execute.
        enemy: Enemy state.
        player: Player state.
    
    Returns:
        Dictionary describing the action taken.
    """
    result = {'intent': intent.intent_type.value, 'details': {}}
    
    if intent.intent_type == Intent.ATTACK:
        total_damage = 0
        for _ in range(intent.hits):
            # Calculate damage with strength
            damage = intent.damage + enemy.strength
            
            # Apply vulnerability (50% more)
            if player.artifact > 0 and intent.hits == 1:
                pass  # Artifact doesn't affect damage
            
            # Apply damage to player
            blocked = min(player.block, damage)
            actual = damage - blocked
            player.block -= blocked
            player.hp -= actual
            total_damage += actual
        
        result['details'] = {
            'base_damage': intent.damage,
            'hits': intent.hits,
            'total_damage': total_damage
        }
    
    elif intent.intent_type == Intent.DEFEND:
        enemy.block += intent.block
        result['details'] = {'block_gained': intent.block}
    
    elif intent.intent_type == Intent.BUFF:
        enemy.strength += intent.strength_gain
        result['details'] = {'strength_gained': intent.strength_gain}
    
    elif intent.intent_type == Intent.DEBUFF:
        if player.artifact > 0:
            player.artifact -= 1
            result['details'] = {'blocked_by_artifact': True}
        else:
            if intent.debuff_type == 'weak':
                player.weak = getattr(player, 'weak', 0) + intent.debuff_stacks
            elif intent.debuff_type == 'vulnerable':
                player.vulnerable = getattr(player, 'vulnerable', 0) + intent.debuff_stacks
            elif intent.debuff_type == 'frail':
                player.frail = getattr(player, 'frail', 0) + intent.debuff_stacks
            result['details'] = {
                'debuff': intent.debuff_type,
                'stacks': intent.debuff_stacks
            }
    
    return result


# ============================================================================
# ENCOUNTER SUITE RUNNER
# ============================================================================

def run_encounter_suite(
    simulate_fn: Callable,
    rng: np.random.Generator,
    runs_per_encounter: int = 100
) -> Dict[str, Dict]:
    """
    Run full encounter suite for calibration.
    
    Args:
        simulate_fn: Simulation function that takes (rng, encounter) params.
        rng: Random number generator.
        runs_per_encounter: Number of runs per encounter type.
    
    Returns:
        Dictionary of encounter name to results.
    """
    results = {}
    
    for encounter in CANONICAL_ENCOUNTERS:
        encounter_results = {
            'wins': 0,
            'turns': [],
            'damage_taken': [],
            'encounter_type': encounter.encounter_type.value
        }
        
        for i in range(runs_per_encounter):
            # Create child RNG for this run
            child_seed = rng.integers(0, 2**31)
            child_rng = np.random.default_rng(child_seed)
            
            result = simulate_fn(child_rng, encounter)
            
            if result.get('win', False):
                encounter_results['wins'] += 1
            encounter_results['turns'].append(result.get('turns', 0))
            encounter_results['damage_taken'].append(result.get('damage_taken', 0))
        
        # Compute summary statistics
        encounter_results['win_rate'] = encounter_results['wins'] / runs_per_encounter
        encounter_results['mean_turns'] = np.mean(encounter_results['turns'])
        encounter_results['mean_damage'] = np.mean(encounter_results['damage_taken'])
        encounter_results['std_damage'] = np.std(encounter_results['damage_taken'])
        
        results[encounter.name] = encounter_results
    
    return results
