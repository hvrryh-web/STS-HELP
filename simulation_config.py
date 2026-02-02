"""
Monte Carlo Simulation Configuration Module.

Provides explicit, variable-driven heuristics and configuration for the
quantized economic data simulation system.

This module addresses the upgrade requirements for:
- Explicit, variable-driven heuristics (no implicit assumptions)
- Improved scenario branching
- Higher-order probabilistic evaluation
- Clear separation of data, logic, and scoring layers

All parameters are documented with their assumptions and constraints.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
import hashlib
import json


# ============================================================================
# SIMULATION SCENARIO TYPES
# ============================================================================

class ScenarioType(Enum):
    """Types of simulation scenarios for branching."""
    BASELINE = "baseline"           # Standard starter deck vs single enemy
    UPGRADED_DECK = "upgraded"      # Deck with card upgrades
    RELIC_SYNERGY = "relic"         # Testing specific relic effects
    MULTI_ENEMY = "multi"           # Multi-enemy encounters
    BOSS_FIGHT = "boss"             # Boss-level encounters
    ASCENSION = "ascension"         # Ascension difficulty scaling


class EnemyProfile(Enum):
    """Standardized enemy profiles for consistent testing."""
    BURST_ATTACKER = "burst"        # High damage, low HP
    DEBUFFER = "debuffer"           # Applies debuffs before attacking
    SCALING_THREAT = "scaling"      # Gains strength over time
    DEFENSIVE = "defensive"         # Blocks and counter-attacks
    BOSS_PHASE = "boss"             # Phase-switching behavior


class DifficultyTier(Enum):
    """Difficulty tiers for calibration."""
    EASY = "easy"       # Low HP, weak attacks
    NORMAL = "normal"   # Balanced
    HARD = "hard"       # High HP, strong attacks
    ELITE = "elite"     # Elite-level difficulty
    BOSS = "boss"       # Boss-level difficulty


# ============================================================================
# HEURISTIC PARAMETERS
# All heuristics are explicit and variable-driven
# ============================================================================

@dataclass
class CardValueHeuristics:
    """
    Heuristics for card value evaluation.
    
    These are explicit parameters that can be tuned and documented.
    No implicit assumptions - all multipliers are configurable.
    """
    # Damage value multipliers
    damage_per_hp: float = 1.0              # Value per point of damage dealt
    vulnerable_multiplier: float = 1.5       # Damage multiplier when enemy is vulnerable
    
    # Block value multipliers
    block_when_threatened: float = 1.2       # Block value when enemy intends to attack
    block_when_safe: float = 0.3             # Block value when enemy is buffing
    
    # Strength scaling
    strength_per_attack: float = 0.5         # Value per future attack benefiting from strength
    double_strength_multiplier: float = 3.0  # Value multiplier for Limit Break effect
    
    # Debuff values
    vulnerable_stack_value: float = 5.0      # Value per stack of vulnerable applied
    weak_stack_value: float = 3.0            # Value per stack of weak applied
    
    # Draw and energy
    draw_value: float = 4.0                  # Value per card drawn
    energy_value: float = 3.0                # Value per energy gained
    
    # Energy efficiency
    apply_energy_efficiency: bool = True     # Divide value by cost if True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'damage_per_hp': self.damage_per_hp,
            'vulnerable_multiplier': self.vulnerable_multiplier,
            'block_when_threatened': self.block_when_threatened,
            'block_when_safe': self.block_when_safe,
            'strength_per_attack': self.strength_per_attack,
            'double_strength_multiplier': self.double_strength_multiplier,
            'vulnerable_stack_value': self.vulnerable_stack_value,
            'weak_stack_value': self.weak_stack_value,
            'draw_value': self.draw_value,
            'energy_value': self.energy_value,
            'apply_energy_efficiency': self.apply_energy_efficiency,
        }


@dataclass
class EnemyBehaviorHeuristics:
    """
    Heuristics for enemy AI behavior simulation.
    
    Documents assumptions about enemy action selection.
    """
    # Attack probability by phase
    attack_probability_early: float = 0.7    # Probability of attacking in early turns
    attack_probability_late: float = 0.8     # Probability of attacking in late turns
    
    # Damage scaling
    base_damage_turn1: int = 18              # First turn damage (strong opening)
    base_damage_normal: int = 14             # Normal attack damage
    damage_scaling_per_turn: int = 3         # Damage increase every 2 turns
    
    # Buff behavior
    buff_probability: float = 0.15           # Probability of buffing instead of attacking
    strength_per_buff: int = 3               # Strength gained per buff
    
    # Defense behavior
    defend_probability: float = 0.15         # Probability of defending
    block_per_defend: int = 12               # Block gained per defend
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'attack_probability_early': self.attack_probability_early,
            'attack_probability_late': self.attack_probability_late,
            'base_damage_turn1': self.base_damage_turn1,
            'base_damage_normal': self.base_damage_normal,
            'damage_scaling_per_turn': self.damage_scaling_per_turn,
            'buff_probability': self.buff_probability,
            'strength_per_buff': self.strength_per_buff,
            'defend_probability': self.defend_probability,
            'block_per_defend': self.block_per_defend,
        }


@dataclass
class ScoringHeuristics:
    """
    Heuristics for decision-value scoring (EV, PV, GGV, etc.).
    
    Separates scoring logic from simulation logic.
    """
    # Base prediction value
    baseline_prediction: float = 50.0        # PV baseline
    
    # APV adjustment
    apv_lambda: float = 0.3                  # Learning rate for APV adjustment
    
    # Risk penalties/bonuses
    cgv_beta: float = 0.1                    # CGV variance penalty
    
    # Tail percentiles
    greed_percentile: float = 95.0           # GGV percentile (upside tail)
    scared_percentile: float = 5.0           # SGV percentile (downside tail)
    jackpot_percentile: float = 90.0         # JV threshold percentile
    
    # Reward function
    win_reward: int = 100                    # Reward for winning
    damage_penalty_per_hp: float = 1.0       # Penalty per HP lost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'baseline_prediction': self.baseline_prediction,
            'apv_lambda': self.apv_lambda,
            'cgv_beta': self.cgv_beta,
            'greed_percentile': self.greed_percentile,
            'scared_percentile': self.scared_percentile,
            'jackpot_percentile': self.jackpot_percentile,
            'win_reward': self.win_reward,
            'damage_penalty_per_hp': self.damage_penalty_per_hp,
        }


# ============================================================================
# SIMULATION CONFIGURATION
# ============================================================================

@dataclass
class SimulationConfig:
    """
    Complete simulation configuration with all parameters explicit.
    
    This is the primary configuration class for Monte Carlo simulations.
    All parameters have documented defaults and constraints.
    """
    # PRNG Configuration
    root_seed: int = 42                      # Root seed for reproducibility
    
    # Batch Configuration
    runs_per_batch: int = 1000               # Runs per batch
    batch_count: int = 10                    # Number of batches
    
    # Combat Configuration
    enemy_hp: int = 120                      # Enemy starting HP
    max_turns: int = 50                      # Maximum turns before timeout
    
    # Player Configuration
    player_hp: int = 80                      # Player starting HP (Ironclad default)
    player_energy: int = 3                   # Energy per turn
    
    # Scenario Configuration
    scenario_type: ScenarioType = ScenarioType.BASELINE
    enemy_profile: EnemyProfile = EnemyProfile.SCALING_THREAT
    difficulty_tier: DifficultyTier = DifficultyTier.ELITE
    
    # Heuristic Configurations
    card_heuristics: CardValueHeuristics = field(default_factory=CardValueHeuristics)
    enemy_heuristics: EnemyBehaviorHeuristics = field(default_factory=EnemyBehaviorHeuristics)
    scoring_heuristics: ScoringHeuristics = field(default_factory=ScoringHeuristics)
    
    # Convergence Configuration
    convergence_threshold: float = 0.02      # 2% change threshold
    min_runs_for_convergence: int = 100      # Minimum runs before checking convergence
    
    # Validation Bounds
    win_rate_bounds: Tuple[float, float] = (0.05, 0.95)
    mean_turns_bounds: Tuple[float, float] = (3, 50)
    mean_damage_bounds: Tuple[float, float] = (0, 100)
    
    # Output Configuration
    output_format: str = "parquet"           # Output format (parquet, json, csv)
    generate_charts: bool = True             # Whether to generate visualization charts
    generate_pdf_report: bool = True         # Whether to generate PDF report
    generate_excel_report: bool = True       # Whether to generate Excel report
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging and serialization."""
        return {
            'root_seed': self.root_seed,
            'runs_per_batch': self.runs_per_batch,
            'batch_count': self.batch_count,
            'enemy_hp': self.enemy_hp,
            'max_turns': self.max_turns,
            'player_hp': self.player_hp,
            'player_energy': self.player_energy,
            'scenario_type': self.scenario_type.value,
            'enemy_profile': self.enemy_profile.value,
            'difficulty_tier': self.difficulty_tier.value,
            'card_heuristics': self.card_heuristics.to_dict(),
            'enemy_heuristics': self.enemy_heuristics.to_dict(),
            'scoring_heuristics': self.scoring_heuristics.to_dict(),
            'convergence_threshold': self.convergence_threshold,
            'min_runs_for_convergence': self.min_runs_for_convergence,
            'win_rate_bounds': self.win_rate_bounds,
            'mean_turns_bounds': self.mean_turns_bounds,
            'mean_damage_bounds': self.mean_damage_bounds,
            'output_format': self.output_format,
            'generate_charts': self.generate_charts,
            'generate_pdf_report': self.generate_pdf_report,
            'generate_excel_report': self.generate_excel_report,
        }
    
    def get_config_hash(self) -> str:
        """
        Get SHA256 hash of configuration for versioning.
        
        Returns first 16 characters of hash for brevity.
        """
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationConfig':
        """Create configuration from dictionary."""
        # Extract nested heuristics
        card_heuristics = CardValueHeuristics(**data.pop('card_heuristics', {}))
        enemy_heuristics = EnemyBehaviorHeuristics(**data.pop('enemy_heuristics', {}))
        scoring_heuristics = ScoringHeuristics(**data.pop('scoring_heuristics', {}))
        
        # Convert enums
        if 'scenario_type' in data:
            data['scenario_type'] = ScenarioType(data['scenario_type'])
        if 'enemy_profile' in data:
            data['enemy_profile'] = EnemyProfile(data['enemy_profile'])
        if 'difficulty_tier' in data:
            data['difficulty_tier'] = DifficultyTier(data['difficulty_tier'])
        
        # Convert tuples
        for key in ['win_rate_bounds', 'mean_turns_bounds', 'mean_damage_bounds']:
            if key in data and isinstance(data[key], list):
                data[key] = tuple(data[key])
        
        return cls(
            card_heuristics=card_heuristics,
            enemy_heuristics=enemy_heuristics,
            scoring_heuristics=scoring_heuristics,
            **data
        )


# ============================================================================
# SCENARIO PRESETS
# Pre-defined configurations for common simulation scenarios
# ============================================================================

def get_baseline_config(seed: int = 42, runs: int = 1000) -> SimulationConfig:
    """Get baseline configuration for standard simulations."""
    return SimulationConfig(
        root_seed=seed,
        runs_per_batch=runs,
        batch_count=1,
        scenario_type=ScenarioType.BASELINE,
        difficulty_tier=DifficultyTier.ELITE,
    )


def get_calibration_config(seed: int = 42) -> SimulationConfig:
    """Get configuration for calibration runs."""
    return SimulationConfig(
        root_seed=seed,
        runs_per_batch=5000,
        batch_count=4,
        scenario_type=ScenarioType.BASELINE,
        difficulty_tier=DifficultyTier.ELITE,
        convergence_threshold=0.01,  # Tighter convergence for calibration
    )


def get_stress_test_config(seed: int = 42) -> SimulationConfig:
    """Get configuration for stress testing (hard difficulty)."""
    return SimulationConfig(
        root_seed=seed,
        runs_per_batch=1000,
        batch_count=2,
        enemy_hp=150,
        scenario_type=ScenarioType.BASELINE,
        difficulty_tier=DifficultyTier.BOSS,
        enemy_heuristics=EnemyBehaviorHeuristics(
            base_damage_turn1=25,
            base_damage_normal=18,
            damage_scaling_per_turn=4,
        ),
    )


def get_quick_test_config(seed: int = 42) -> SimulationConfig:
    """Get configuration for quick validation tests."""
    return SimulationConfig(
        root_seed=seed,
        runs_per_batch=100,
        batch_count=1,
        scenario_type=ScenarioType.BASELINE,
        generate_charts=False,
        generate_pdf_report=False,
        generate_excel_report=False,
    )


# ============================================================================
# DATA GAPS AND ASSUMPTIONS DOCUMENTATION
# ============================================================================

DATA_GAPS = [
    {
        'id': 'DG-001',
        'category': 'Enemy Behavior',
        'description': 'Enemy intent patterns are probabilistic proxies, not exact per-enemy scripts',
        'impact': 'Low',
        'mitigation': 'Calibrated against canonical encounter types',
    },
    {
        'id': 'DG-002',
        'category': 'Card Pool',
        'description': 'Only starter deck and basic cards are modeled',
        'impact': 'Medium',
        'mitigation': 'Card addition framework exists but not fully populated',
    },
    {
        'id': 'DG-003',
        'category': 'Multi-Target',
        'description': 'Multi-enemy targeting not implemented',
        'impact': 'Medium',
        'mitigation': 'Encounter suite includes multi-enemy definitions',
    },
    {
        'id': 'DG-004',
        'category': 'Relic Effects',
        'description': 'Most relic effects not fully simulated',
        'impact': 'Medium',
        'mitigation': 'Relic system framework exists for future implementation',
    },
    {
        'id': 'DG-005',
        'category': 'Card Upgrades',
        'description': 'Card upgrade effects not simulated',
        'impact': 'Low',
        'mitigation': 'Card model supports upgrade flag',
    },
    {
        'id': 'DG-006',
        'category': 'Events/Shops',
        'description': 'Non-combat encounters not modeled',
        'impact': 'Medium',
        'mitigation': 'Out of scope for combat simulation',
    },
    {
        'id': 'DG-007',
        'category': 'Ascension',
        'description': 'Ascension modifiers not fully implemented',
        'impact': 'Low',
        'mitigation': 'Encounter suite supports ascension HP scaling',
    },
]


ASSUMPTIONS = [
    {
        'id': 'A-001',
        'category': 'Combat',
        'assumption': 'Player always plays optimal card from hand',
        'justification': 'Heuristic-based selection approximates optimal play',
    },
    {
        'id': 'A-002',
        'category': 'Deck',
        'assumption': 'Deck is shuffled uniformly at random',
        'justification': 'Uses numpy SeedSequence for cryptographic-quality randomness',
    },
    {
        'id': 'A-003',
        'category': 'Enemy',
        'assumption': 'Enemy damage includes strength but not other modifiers',
        'justification': 'Simplified model sufficient for calibration',
    },
    {
        'id': 'A-004',
        'category': 'Artifact',
        'assumption': 'Artifact blocks one debuff application event, not magnitude',
        'justification': 'Matches official game mechanics',
    },
    {
        'id': 'A-005',
        'category': 'Block',
        'assumption': 'Block resets to 0 at start of player turn',
        'justification': 'Standard game behavior (no Barricade)',
    },
    {
        'id': 'A-006',
        'category': 'Poison',
        'assumption': 'Poison triggers at start of enemy turn, bypasses block',
        'justification': 'Matches official game mechanics',
    },
]


def get_data_gaps() -> List[Dict[str, str]]:
    """Get list of documented data gaps."""
    return DATA_GAPS.copy()


def get_assumptions() -> List[Dict[str, str]]:
    """Get list of documented assumptions."""
    return ASSUMPTIONS.copy()


def get_documentation_report() -> Dict[str, Any]:
    """
    Generate a documentation report of all heuristics, assumptions, and data gaps.
    
    Returns:
        Dictionary containing complete documentation.
    """
    return {
        'version': '1.0.0',
        'heuristics': {
            'card_value': CardValueHeuristics().to_dict(),
            'enemy_behavior': EnemyBehaviorHeuristics().to_dict(),
            'scoring': ScoringHeuristics().to_dict(),
        },
        'assumptions': ASSUMPTIONS,
        'data_gaps': DATA_GAPS,
        'scenario_types': [e.value for e in ScenarioType],
        'enemy_profiles': [e.value for e in EnemyProfile],
        'difficulty_tiers': [e.value for e in DifficultyTier],
    }
