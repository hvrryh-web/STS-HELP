"""
Game Data Mechanical Power Ranking System.

Implements a Base Value (BV) metric system derived from community tier lists,
advanced player expertise, and mechanical analysis of Slay the Spire.

Sources:
- Unduel community card/relic tier lists
- SpireSpy expert rankings
- GamingScan Ascension 20 guides
- High-level player consensus (streamer meta)

The Base Value (BV) represents a card/relic's intrinsic power level on a 0-100 scale:
- 90-100: S-Tier (run-defining, always take)
- 75-89: A-Tier (very strong, usually take)
- 60-74: B-Tier (solid, context-dependent)
- 45-59: C-Tier (situational, archetype-specific)
- 30-44: D-Tier (weak, rarely take)
- 0-29: F-Tier (actively harmful, skip)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path


class PowerTier(Enum):
    """Power tier classification."""
    S = "S"  # 90-100: Run-defining
    A = "A"  # 75-89: Very strong
    B = "B"  # 60-74: Solid
    C = "C"  # 45-59: Situational
    D = "D"  # 30-44: Weak
    F = "F"  # 0-29: Skip


class ValueCategory(Enum):
    """Categories of value a card/relic provides."""
    DAMAGE = "damage"           # Direct damage output
    BLOCK = "block"             # Defensive capability
    SCALING = "scaling"         # Long-term power growth
    DRAW = "draw"               # Card draw/cycling
    ENERGY = "energy"           # Energy generation
    UTILITY = "utility"         # Flexibility, tutoring
    SUSTAIN = "sustain"         # Healing, survivability
    DEBUFF = "debuff"           # Enemy debuffing
    AOE = "aoe"                 # Multi-target capability


@dataclass
class BaseValue:
    """
    Base Value rating for a game element.
    
    Attributes:
        score: Numeric score 0-100.
        tier: Power tier classification.
        vacuum_score: Score in a vacuum (no synergies).
        synergy_potential: How much the score can increase with synergies.
        floor_dependency: How much value varies by floor/act.
        categories: Which value categories this provides.
        notes: Expert notes on usage.
    """
    score: float
    tier: PowerTier
    vacuum_score: float = 0.0
    synergy_potential: float = 0.0
    floor_dependency: float = 0.0  # 0 = consistent, 1 = highly variable
    categories: List[ValueCategory] = field(default_factory=list)
    notes: str = ""
    
    @classmethod
    def from_score(cls, score: float, **kwargs) -> 'BaseValue':
        """Create BaseValue from a numeric score."""
        if score >= 90:
            tier = PowerTier.S
        elif score >= 75:
            tier = PowerTier.A
        elif score >= 60:
            tier = PowerTier.B
        elif score >= 45:
            tier = PowerTier.C
        elif score >= 30:
            tier = PowerTier.D
        else:
            tier = PowerTier.F
        
        return cls(score=score, tier=tier, vacuum_score=score, **kwargs)


# =============================================================================
# IRONCLAD CARD BASE VALUES
# Derived from community consensus and mechanical analysis
# =============================================================================

IRONCLAD_CARD_VALUES: Dict[str, BaseValue] = {
    # === S-TIER (90-100) ===
    "Corruption": BaseValue.from_score(
        98, synergy_potential=0.9,
        categories=[ValueCategory.SCALING, ValueCategory.ENERGY],
        notes="Makes all Skills cost 0. Enables infinite block with Feel No Pain. "
              "Core of exhaust archetype. Top-tier with Dead Branch relic."
    ),
    "Offering": BaseValue.from_score(
        96, synergy_potential=0.3,
        categories=[ValueCategory.DRAW, ValueCategory.ENERGY],
        notes="2 Energy + 3 cards for 6 HP. Best tempo card in the game. "
              "Take in almost every deck. Enables turn 1 power plays."
    ),
    "Reaper": BaseValue.from_score(
        94, synergy_potential=0.5,
        categories=[ValueCategory.DAMAGE, ValueCategory.SUSTAIN, ValueCategory.AOE],
        notes="Heals based on unblocked damage to ALL enemies. "
              "Scales with Strength. Core sustain for Ironclad."
    ),
    "Feed": BaseValue.from_score(
        92, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.SUSTAIN],
        notes="Permanent Max HP gain. Essential for Ascension 20 survival. "
              "Best used on non-minion enemies early in run."
    ),
    "Immolate": BaseValue.from_score(
        91, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE, ValueCategory.AOE],
        notes="21 damage to ALL enemies. Burn downside is minimal. "
              "Best AoE attack in the game for Ironclad."
    ),
    "Impervious": BaseValue.from_score(
        90, synergy_potential=0.4,
        categories=[ValueCategory.BLOCK],
        notes="30 Block. Best single-card defensive option. "
              "Essential for boss fights. Works with Body Slam."
    ),
    
    # === A-TIER (75-89) ===
    "Battle Trance": BaseValue.from_score(
        88, synergy_potential=0.2,
        categories=[ValueCategory.DRAW],
        notes="Draw 3 for 0 energy. Downside rarely matters. "
              "Excellent consistency card."
    ),
    "Dark Embrace": BaseValue.from_score(
        86, synergy_potential=0.8,
        categories=[ValueCategory.DRAW, ValueCategory.SCALING],
        notes="Draw on exhaust. Core of exhaust archetype. "
              "Exceptional with Corruption, Second Wind."
    ),
    "Shockwave": BaseValue.from_score(
        85, synergy_potential=0.3,
        categories=[ValueCategory.DEBUFF, ValueCategory.AOE],
        notes="3 Weak + 3 Vulnerable to ALL. Best debuff card. "
              "Reduces incoming damage by ~44% for 3 turns."
    ),
    "Feel No Pain": BaseValue.from_score(
        84, synergy_potential=0.9,
        categories=[ValueCategory.BLOCK, ValueCategory.SCALING],
        notes="3 Block per exhaust. Infinite block with Corruption. "
              "Core defensive scaling for exhaust builds."
    ),
    "Demon Form": BaseValue.from_score(
        83, synergy_potential=0.6, floor_dependency=0.7,
        categories=[ValueCategory.SCALING],
        notes="2 Strength per turn. Slow but powerful scaling. "
              "Best in long fights (bosses). Worse in hallways."
    ),
    "Limit Break": BaseValue.from_score(
        82, synergy_potential=0.8,
        categories=[ValueCategory.SCALING],
        notes="Double Strength. Insane with existing Strength. "
              "Needs setup but provides exponential scaling."
    ),
    "Uppercut": BaseValue.from_score(
        80, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.DEBUFF],
        notes="13 damage + Weak + Vulnerable. Versatile attack. "
              "Good in any deck. Premium common card."
    ),
    "Second Wind": BaseValue.from_score(
        79, synergy_potential=0.7,
        categories=[ValueCategory.BLOCK],
        notes="Exhaust non-attacks, gain block per exhaust. "
              "Excellent with Feel No Pain, Dark Embrace."
    ),
    "Shrug It Off": BaseValue.from_score(
        78, synergy_potential=0.1,
        categories=[ValueCategory.BLOCK, ValueCategory.DRAW],
        notes="8 Block + draw. Best common defensive card. "
              "Take early, stays relevant all run."
    ),
    "Flame Barrier": BaseValue.from_score(
        76, synergy_potential=0.3,
        categories=[ValueCategory.BLOCK, ValueCategory.DAMAGE],
        notes="12 Block + thorns. Great vs multi-hit enemies. "
              "Gremlin Nob, Heart, Time Eater counter."
    ),
    "Spot Weakness": BaseValue.from_score(
        75, synergy_potential=0.5,
        categories=[ValueCategory.SCALING],
        notes="Conditional 3 Strength. Usually active 60%+ of turns. "
              "Efficient Strength source when it works."
    ),
    
    # === B-TIER (60-74) ===
    "Inflame": BaseValue.from_score(
        72, synergy_potential=0.4,
        categories=[ValueCategory.SCALING],
        notes="2 Strength. Simple, effective. Good early pickup. "
              "Less impressive than scaling options."
    ),
    "Heavy Blade": BaseValue.from_score(
        70, synergy_potential=0.9, floor_dependency=0.5,
        categories=[ValueCategory.DAMAGE],
        notes="14 damage, Strength x3 (x5 upgraded). Amazing with Strength. "
              "Weak without Strength stacking."
    ),
    "Carnage": BaseValue.from_score(
        68, synergy_potential=0.1,
        categories=[ValueCategory.DAMAGE],
        notes="20 damage, Ethereal. Solid front-loaded damage. "
              "Best early, worse in long fights."
    ),
    "Pommel Strike": BaseValue.from_score(
        66, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.DRAW],
        notes="9 damage + draw. Replaces itself. Solid filler. "
              "Good for deck cycling."
    ),
    "Clothesline": BaseValue.from_score(
        64, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.DEBUFF],
        notes="12 damage + 2 Weak. Decent, but 2 cost is steep. "
              "Uppercut is usually better."
    ),
    "Whirlwind": BaseValue.from_score(
        62, synergy_potential=0.6, floor_dependency=0.6,
        categories=[ValueCategory.DAMAGE, ValueCategory.AOE],
        notes="X-cost AoE. Great with extra energy. "
              "Needs energy support to shine."
    ),
    "Barricade": BaseValue.from_score(
        60, synergy_potential=0.7, floor_dependency=0.7,
        categories=[ValueCategory.SCALING, ValueCategory.BLOCK],
        notes="Retain Block. Amazing in block builds. "
              "3 cost is prohibitive without energy."
    ),
    
    # === C-TIER (45-59) ===
    "Iron Wave": BaseValue.from_score(
        55, synergy_potential=0.1,
        categories=[ValueCategory.DAMAGE, ValueCategory.BLOCK],
        notes="5 damage + 5 block. Mediocre but flexible. "
              "Neither good at offense nor defense."
    ),
    "Headbutt": BaseValue.from_score(
        52, synergy_potential=0.4,
        categories=[ValueCategory.DAMAGE, ValueCategory.UTILITY],
        notes="9 damage + setup top deck. Combo enabler. "
              "Good with specific cards (Limit Break)."
    ),
    "Twin Strike": BaseValue.from_score(
        50, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE],
        notes="5x2 damage. Multi-hit for Strength scaling. "
              "Mediocre without Strength."
    ),
    "Anger": BaseValue.from_score(
        48, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE],
        notes="0 cost, adds copy. Deck dilution risk. "
              "Can be good early, bad late."
    ),
    "Flex": BaseValue.from_score(
        45, synergy_potential=0.3,
        categories=[ValueCategory.SCALING],
        notes="Temporary Strength. Only good with Limit Break. "
              "Usually worse than permanent Strength."
    ),
    
    # === D-TIER (30-44) ===
    "Cleave": BaseValue.from_score(
        42, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.AOE],
        notes="8 AoE damage. Worse than Immolate in every way. "
              "Only take if desperate for AoE."
    ),
    "Sword Boomerang": BaseValue.from_score(
        38, synergy_potential=0.5,
        categories=[ValueCategory.DAMAGE],
        notes="3x3 random damage. Inaccurate, Strength-dependent. "
              "Awkward targeting limits usefulness."
    ),
    "Wild Strike": BaseValue.from_score(
        35, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE],
        notes="12 damage + Wound. Wound is significant downside. "
              "Only good with Evolve."
    ),
    "Clash": BaseValue.from_score(
        32, synergy_potential=0.1,
        categories=[ValueCategory.DAMAGE],
        notes="0 cost 14 damage, requires all attacks. "
              "Almost never playable. Trap card."
    ),
    
    # === F-TIER (0-29) - Skip these ===
    "Strike": BaseValue.from_score(
        20, synergy_potential=0.0,
        categories=[ValueCategory.DAMAGE],
        notes="Starter card. Remove ASAP. 6 damage is pitiful."
    ),
    "Defend": BaseValue.from_score(
        22, synergy_potential=0.0,
        categories=[ValueCategory.BLOCK],
        notes="Starter card. Remove when possible. "
              "5 block is barely functional."
    ),
}


# =============================================================================
# SILENT CARD BASE VALUES
# =============================================================================

SILENT_CARD_VALUES: Dict[str, BaseValue] = {
    # === S-TIER ===
    "Wraith Form": BaseValue.from_score(
        99, synergy_potential=0.3, floor_dependency=0.4,
        categories=[ValueCategory.BLOCK, ValueCategory.SCALING],
        notes="Intangible for 2-3 turns. Best defensive card in game. "
              "Dexterity loss manageable with Orange Pellets or short fights."
    ),
    "Adrenaline": BaseValue.from_score(
        97, synergy_potential=0.2,
        categories=[ValueCategory.DRAW, ValueCategory.ENERGY],
        notes="2 Energy + 2 cards + 0 cost. Best skill in the game. "
              "Always take, enables any strategy."
    ),
    "After Image": BaseValue.from_score(
        95, synergy_potential=0.4,
        categories=[ValueCategory.BLOCK, ValueCategory.SCALING],
        notes="1 Block per card played. Insane with shiv/low-cost decks. "
              "Passive defense that scales infinitely."
    ),
    "Corpse Explosion": BaseValue.from_score(
        93, synergy_potential=0.5,
        categories=[ValueCategory.DAMAGE, ValueCategory.AOE],
        notes="Enemy explodes for its max HP. AoE solution for poison. "
              "Trivializes multi-enemy fights."
    ),
    "Catalyst": BaseValue.from_score(
        92, synergy_potential=0.9,
        categories=[ValueCategory.DAMAGE, ValueCategory.SCALING],
        notes="Double/Triple poison. Core of poison archetype. "
              "Exponential damage scaling."
    ),
    "Well-Laid Plans": BaseValue.from_score(
        91, synergy_potential=0.3,
        categories=[ValueCategory.UTILITY],
        notes="Retain 1-2 cards. Incredible consistency power. "
              "Save key cards for when needed."
    ),
    "Malaise": BaseValue.from_score(
        90, synergy_potential=0.3,
        categories=[ValueCategory.DEBUFF],
        notes="X Weak + lose X Strength permanently. "
              "Boss killer. Neutralizes scaling enemies."
    ),
    
    # === A-TIER ===
    "Footwork": BaseValue.from_score(
        88, synergy_potential=0.5,
        categories=[ValueCategory.SCALING, ValueCategory.BLOCK],
        notes="2-3 Dexterity. Best defensive scaling. "
              "Stacks multiplicatively with block cards."
    ),
    "Piercing Wail": BaseValue.from_score(
        86, synergy_potential=0.2,
        categories=[ValueCategory.DEBUFF, ValueCategory.AOE],
        notes="6 Strength loss to ALL. Emergency defense. "
              "Can prevent 40+ damage in one card."
    ),
    "Blade Dance": BaseValue.from_score(
        84, synergy_potential=0.7,
        categories=[ValueCategory.DAMAGE],
        notes="3-4 Shivs. Core of shiv archetype. "
              "Insane with Accuracy, After Image, Kunai."
    ),
    "Glass Knife": BaseValue.from_score(
        82, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE],
        notes="8x2 damage, decreases per use. Great front-loaded. "
              "Best early in combat."
    ),
    "Noxious Fumes": BaseValue.from_score(
        80, synergy_potential=0.6,
        categories=[ValueCategory.DAMAGE, ValueCategory.SCALING],
        notes="2-3 poison to ALL per turn. Passive scaling. "
              "Core of poison builds, weak standalone."
    ),
    "Backflip": BaseValue.from_score(
        78, synergy_potential=0.2,
        categories=[ValueCategory.BLOCK, ValueCategory.DRAW],
        notes="5 Block + Draw 2. Excellent common. "
              "Stays relevant entire run."
    ),
    "Acrobatics": BaseValue.from_score(
        76, synergy_potential=0.4,
        categories=[ValueCategory.DRAW],
        notes="Draw 3, discard 1. Great filtering. "
              "Synergizes with discard effects."
    ),
    "Deadly Poison": BaseValue.from_score(
        75, synergy_potential=0.5,
        categories=[ValueCategory.DAMAGE],
        notes="5-7 poison. Basic poison application. "
              "Good early, replaced by better poison cards."
    ),
    
    # === B-TIER ===
    "Dash": BaseValue.from_score(
        72, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.BLOCK],
        notes="10 damage + 10 block. Versatile. "
              "Good filler but not exciting."
    ),
    "Leg Sweep": BaseValue.from_score(
        70, synergy_potential=0.2,
        categories=[ValueCategory.BLOCK, ValueCategory.DEBUFF],
        notes="Block + Weak. Solid defensive option. "
              "2 cost is slightly expensive."
    ),
    "Accuracy": BaseValue.from_score(
        68, synergy_potential=0.9,
        categories=[ValueCategory.SCALING],
        notes="Shivs deal 4-6 more damage. Build-around. "
              "Amazing with shivs, useless without."
    ),
    "Predator": BaseValue.from_score(
        65, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.DRAW],
        notes="15 damage + draw next turn. Front-loaded damage. "
              "Good for finishing fights fast."
    ),
    "Cloak and Dagger": BaseValue.from_score(
        62, synergy_potential=0.5,
        categories=[ValueCategory.BLOCK, ValueCategory.DAMAGE],
        notes="Block + Shivs. Defensive shiv generation. "
              "Versatile for shiv builds."
    ),
    "Bouncing Flask": BaseValue.from_score(
        60, synergy_potential=0.4,
        categories=[ValueCategory.DAMAGE, ValueCategory.AOE],
        notes="3 poison x3 targets. AoE poison application. "
              "Good for multi-enemy, mediocre single target."
    ),
}


# =============================================================================
# DEFECT CARD BASE VALUES
# =============================================================================

DEFECT_CARD_VALUES: Dict[str, BaseValue] = {
    # === S-TIER ===
    "Seek": BaseValue.from_score(
        98, synergy_potential=0.4,
        categories=[ValueCategory.UTILITY],
        notes="Choose 1-2 cards from draw pile. Best tutor. "
              "Finds answers, enables combos, 0 cost upgraded."
    ),
    "Echo Form": BaseValue.from_score(
        97, synergy_potential=0.5, floor_dependency=0.5,
        categories=[ValueCategory.SCALING],
        notes="Play first card twice each turn. Doubles value of everything. "
              "Ethereal is rarely relevant if played smart."
    ),
    "Biased Cognition": BaseValue.from_score(
        95, synergy_potential=0.4,
        categories=[ValueCategory.SCALING],
        notes="+4-5 Focus. Best Focus card. Focus loss is slow. "
              "Win before losing too much, or cleanse with Orange Pellets."
    ),
    "Defragment": BaseValue.from_score(
        93, synergy_potential=0.6,
        categories=[ValueCategory.SCALING],
        notes="+1 Focus. Scales all orbs. Essential for orb builds. "
              "Multiple copies stack well."
    ),
    "Buffer": BaseValue.from_score(
        91, synergy_potential=0.2,
        categories=[ValueCategory.BLOCK],
        notes="Prevent next HP loss. Incredible for Heart, Elites. "
              "Best with Echo Form (double buffer)."
    ),
    "Electrodynamics": BaseValue.from_score(
        90, synergy_potential=0.5,
        categories=[ValueCategory.DAMAGE, ValueCategory.AOE],
        notes="Lightning hits ALL. Solves AoE problem permanently. "
              "Best AoE solution for Defect."
    ),
    
    # === A-TIER ===
    "Glacier": BaseValue.from_score(
        88, synergy_potential=0.4,
        categories=[ValueCategory.BLOCK],
        notes="7 Block + 2 Frost. Best block card. "
              "Generates orbs AND immediate block."
    ),
    "Core Surge": BaseValue.from_score(
        86, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE, ValueCategory.UTILITY],
        notes="11 damage + Artifact. Blocks debuffs. "
              "Great for boss fights with debuffs."
    ),
    "Self Repair": BaseValue.from_score(
        84, synergy_potential=0.2,
        categories=[ValueCategory.SUSTAIN],
        notes="Heal 7-10 end of combat. Consistent sustain. "
              "Less HP loss over a run."
    ),
    "Coolheaded": BaseValue.from_score(
        82, synergy_potential=0.3,
        categories=[ValueCategory.BLOCK, ValueCategory.DRAW],
        notes="Frost + Draw 1-2. Replaces itself + orb. "
              "Excellent common card."
    ),
    "Chill": BaseValue.from_score(
        80, synergy_potential=0.3,
        categories=[ValueCategory.BLOCK],
        notes="Frost per enemy. Great for multi-enemy. "
              "Scales with enemy count."
    ),
    "Cold Snap": BaseValue.from_score(
        78, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE, ValueCategory.BLOCK],
        notes="6 damage + Frost. Attacks AND generates orb. "
              "Good hybrid card."
    ),
    "Hologram": BaseValue.from_score(
        76, synergy_potential=0.4,
        categories=[ValueCategory.UTILITY, ValueCategory.BLOCK],
        notes="Block + retrieve from discard. Recycle key cards. "
              "Flexible and powerful."
    ),
    "Skim": BaseValue.from_score(
        75, synergy_potential=0.2,
        categories=[ValueCategory.DRAW],
        notes="Draw 3-4. Solid draw. "
              "Simple but effective."
    ),
    
    # === B-TIER ===
    "Compile Driver": BaseValue.from_score(
        72, synergy_potential=0.4,
        categories=[ValueCategory.DAMAGE, ValueCategory.DRAW],
        notes="7 damage + draw per orb type. Scales with diversity. "
              "Good in varied orb decks."
    ),
    "Capacitor": BaseValue.from_score(
        70, synergy_potential=0.5,
        categories=[ValueCategory.SCALING],
        notes="+2-3 orb slots. More orbs = more passive effects. "
              "Essential for heavy orb builds."
    ),
    "Consume": BaseValue.from_score(
        68, synergy_potential=0.7,
        categories=[ValueCategory.SCALING],
        notes="-1 slot, +2 Focus. Risk/reward Focus. "
              "Amazing with Inserter relic."
    ),
    "Loop": BaseValue.from_score(
        65, synergy_potential=0.6,
        categories=[ValueCategory.SCALING],
        notes="Trigger first orb passive extra time. Doubles passive. "
              "Great with Frost (double block)."
    ),
    "Fission": BaseValue.from_score(
        62, synergy_potential=0.5,
        categories=[ValueCategory.ENERGY, ValueCategory.DRAW],
        notes="Remove orbs for energy/draw. Orb sacrifice payoff. "
              "Best with Dark orb buildup."
    ),
    "Static Discharge": BaseValue.from_score(
        60, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE],
        notes="Channel Lightning when hit. Reactive damage. "
              "Good vs multi-hit enemies."
    ),
}


# =============================================================================
# WATCHER CARD BASE VALUES
# =============================================================================

WATCHER_CARD_VALUES: Dict[str, BaseValue] = {
    # === S-TIER ===
    "Scrawl": BaseValue.from_score(
        98, synergy_potential=0.3,
        categories=[ValueCategory.DRAW],
        notes="Draw until hand full. Best draw in game at 0 cost. "
              "Enables massive turns."
    ),
    "Omniscience": BaseValue.from_score(
        96, synergy_potential=0.5,
        categories=[ValueCategory.UTILITY, ValueCategory.SCALING],
        notes="Play a card from draw pile twice. Double anything. "
              "Enables crazy combos."
    ),
    "Vault": BaseValue.from_score(
        94, synergy_potential=0.3,
        categories=[ValueCategory.UTILITY, ValueCategory.BLOCK],
        notes="Extra turn. Skip enemy turn essentially. "
              "God-tier defensive option."
    ),
    "Lesson Learned": BaseValue.from_score(
        93, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.SCALING],
        notes="Deal damage, if kills upgrade a card. Permanent value. "
              "Run-long scaling."
    ),
    "Rushdown": BaseValue.from_score(
        91, synergy_potential=0.6,
        categories=[ValueCategory.DRAW, ValueCategory.SCALING],
        notes="Draw 2 when entering Wrath. Free draw on stance. "
              "Core of stance-switching."
    ),
    "Mental Fortress": BaseValue.from_score(
        90, synergy_potential=0.6,
        categories=[ValueCategory.BLOCK, ValueCategory.SCALING],
        notes="4-6 Block per stance change. Passive defense. "
              "Insane with frequent stance switching."
    ),
    
    # === A-TIER ===
    "Tantrum": BaseValue.from_score(
        88, synergy_potential=0.4,
        categories=[ValueCategory.DAMAGE],
        notes="4x3 damage + enter Wrath. Multi-hit Wrath entry. "
              "Premium attack card."
    ),
    "Wallop": BaseValue.from_score(
        86, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE, ValueCategory.BLOCK],
        notes="9 damage, block equal to unblocked damage. "
              "Amazing vs high HP enemies."
    ),
    "Wheel Kick": BaseValue.from_score(
        84, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.DRAW],
        notes="15 damage + Draw 2. Great value. "
              "Premium common attack."
    ),
    "Fear No Evil": BaseValue.from_score(
        82, synergy_potential=0.4,
        categories=[ValueCategory.DAMAGE, ValueCategory.UTILITY],
        notes="8 damage, enter Calm if enemy attacking. "
              "Reactive Calm entry for safety."
    ),
    "Inner Peace": BaseValue.from_score(
        80, synergy_potential=0.4,
        categories=[ValueCategory.DRAW, ValueCategory.UTILITY],
        notes="Enter Calm or draw 3. Flexible. "
              "Great for both effects."
    ),
    "Talk to the Hand": BaseValue.from_score(
        78, synergy_potential=0.4,
        categories=[ValueCategory.DAMAGE, ValueCategory.BLOCK],
        notes="5 damage, gain Block when enemy attacks. "
              "Stacking effect is very strong."
    ),
    "Cut Through Fate": BaseValue.from_score(
        76, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE, ValueCategory.DRAW],
        notes="7 damage + Scry 2 + Draw 1. Incredible value. "
              "Card selection + damage + draw."
    ),
    "Battle Hymn": BaseValue.from_score(
        75, synergy_potential=0.4,
        categories=[ValueCategory.DAMAGE, ValueCategory.SCALING],
        notes="Add Smite to hand each turn. Infinite value. "
              "Slow but powerful."
    ),
    
    # === B-TIER ===
    "Flurry of Blows": BaseValue.from_score(
        72, synergy_potential=0.7,
        categories=[ValueCategory.DAMAGE],
        notes="4 damage, return to hand on stance change. "
              "Infinite with frequent stance switching."
    ),
    "Prostrate": BaseValue.from_score(
        70, synergy_potential=0.3,
        categories=[ValueCategory.BLOCK, ValueCategory.SCALING],
        notes="4 Block + 2 Mantra. Divinity buildup. "
              "Good for Mantra strategies."
    ),
    "Tranquility": BaseValue.from_score(
        68, synergy_potential=0.4,
        categories=[ValueCategory.UTILITY],
        notes="0 cost, enter Calm. Energy generation. "
              "Flexible stance tool."
    ),
    "Sands of Time": BaseValue.from_score(
        65, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE],
        notes="20 damage, retain. Front-loaded retained damage. "
              "Solid finisher."
    ),
    "Brilliance": BaseValue.from_score(
        62, synergy_potential=0.6,
        categories=[ValueCategory.DAMAGE],
        notes="Damage = Mantra gained. Requires Mantra buildup. "
              "High ceiling, high floor."
    ),
    "Sash Whip": BaseValue.from_score(
        60, synergy_potential=0.2,
        categories=[ValueCategory.DAMAGE, ValueCategory.DEBUFF],
        notes="8 damage + Weak if enemy attacking. Conditional. "
              "Decent when it works."
    ),
}


# =============================================================================
# RELIC BASE VALUES
# =============================================================================

RELIC_VALUES: Dict[str, BaseValue] = {
    # === S-TIER RELICS ===
    "Dead Branch": BaseValue.from_score(
        99, synergy_potential=0.9,
        categories=[ValueCategory.SCALING],
        notes="Random card on exhaust. Game-breaking with Corruption. "
              "Enables infinite turns with right setup."
    ),
    "Runic Pyramid": BaseValue.from_score(
        97, synergy_potential=0.5,
        categories=[ValueCategory.UTILITY],
        notes="Retain entire hand. Perfect control of deck. "
              "Enables combos, save answers."
    ),
    "Snecko Eye": BaseValue.from_score(
        96, synergy_potential=0.4,
        categories=[ValueCategory.DRAW, ValueCategory.ENERGY],
        notes="+2 draw, random costs. Average cost reduction. "
              "Best with expensive cards."
    ),
    "Incense Burner": BaseValue.from_score(
        94, synergy_potential=0.2,
        categories=[ValueCategory.BLOCK],
        notes="Intangible every 6 turns. Guaranteed survivability. "
              "Plan big attacks around it."
    ),
    "Gambling Chip": BaseValue.from_score(
        92, synergy_potential=0.3,
        categories=[ValueCategory.UTILITY],
        notes="Mulligan start of combat. Find key cards turn 1. "
              "Massive consistency boost."
    ),
    "Mummified Hand": BaseValue.from_score(
        91, synergy_potential=0.7,
        categories=[ValueCategory.ENERGY],
        notes="Power makes random card free. Amazing for power decks. "
              "Scales with power count."
    ),
    "Coffee Dripper": BaseValue.from_score(
        90, synergy_potential=0.2,
        categories=[ValueCategory.ENERGY],
        notes="+1 Energy, no rest healing. Energy > healing usually. "
              "Take if sustain from other sources."
    ),
    
    # === A-TIER RELICS ===
    "Ice Cream": BaseValue.from_score(
        88, synergy_potential=0.4,
        categories=[ValueCategory.ENERGY],
        notes="Conserve energy between turns. Enables X-cost cards. "
              "Amazing for Defect, Whirlwind decks."
    ),
    "Tough Bandages": BaseValue.from_score(
        86, synergy_potential=0.7,
        categories=[ValueCategory.BLOCK],
        notes="+3 Block on discard. Silent discard synergy. "
              "Builds block passively."
    ),
    "Tungsten Rod": BaseValue.from_score(
        85, synergy_potential=0.2,
        categories=[ValueCategory.BLOCK],
        notes="-1 HP loss. Reduces ALL damage. "
              "Incredible vs multi-hit, poison."
    ),
    "Orange Pellets": BaseValue.from_score(
        84, synergy_potential=0.4,
        categories=[ValueCategory.UTILITY],
        notes="Remove debuffs when playing Power+Attack+Skill. "
              "Counters Biased Cognition, Wraith Form."
    ),
    "Kunai": BaseValue.from_score(
        82, synergy_potential=0.5,
        categories=[ValueCategory.SCALING],
        notes="+1 Dexterity per 3 attacks. Defensive scaling. "
              "Great with multi-attack cards."
    ),
    "Shuriken": BaseValue.from_score(
        81, synergy_potential=0.5,
        categories=[ValueCategory.SCALING],
        notes="+1 Strength per 3 attacks. Offensive scaling. "
              "Great with multi-attack cards."
    ),
    "Ornamental Fan": BaseValue.from_score(
        80, synergy_potential=0.5,
        categories=[ValueCategory.BLOCK],
        notes="+4 Block per 3 attacks. Passive defense. "
              "Works well with attack-heavy decks."
    ),
    "Pantograph": BaseValue.from_score(
        78, synergy_potential=0.1,
        categories=[ValueCategory.SUSTAIN],
        notes="+25 HP at boss fights. Consistent sustain. "
              "Good safety net."
    ),
    "Thread and Needle": BaseValue.from_score(
        76, synergy_potential=0.2,
        categories=[ValueCategory.BLOCK],
        notes="+4 Plated Armor. Permanent block per turn. "
              "Free 4 block forever."
    ),
    "Bag of Preparation": BaseValue.from_score(
        75, synergy_potential=0.2,
        categories=[ValueCategory.DRAW],
        notes="+2 draw turn 1. Better openers. "
              "Simple, always useful."
    ),
    
    # === B-TIER RELICS ===
    "Anchor": BaseValue.from_score(
        72, synergy_potential=0.1,
        categories=[ValueCategory.BLOCK],
        notes="+10 Block turn 1. Safety buffer. "
              "Good early, falls off."
    ),
    "Bag of Marbles": BaseValue.from_score(
        70, synergy_potential=0.2,
        categories=[ValueCategory.DEBUFF],
        notes="+1 Vulnerable to all turn 1. Burst enabler. "
              "Good for fast kills."
    ),
    "Lantern": BaseValue.from_score(
        68, synergy_potential=0.1,
        categories=[ValueCategory.ENERGY],
        notes="+1 Energy turn 1. Enables power plays. "
              "Simple, always useful."
    ),
    "Happy Flower": BaseValue.from_score(
        65, synergy_potential=0.1,
        categories=[ValueCategory.ENERGY],
        notes="+1 Energy every 3 turns. Inconsistent. "
              "Okay, not exciting."
    ),
    "Orichalcum": BaseValue.from_score(
        62, synergy_potential=0.2,
        categories=[ValueCategory.BLOCK],
        notes="+6 Block if no block. Safety net. "
              "Worse than actual block cards."
    ),
    "Vajra": BaseValue.from_score(
        60, synergy_potential=0.3,
        categories=[ValueCategory.DAMAGE],
        notes="+1 Strength. Simple damage boost. "
              "Okay, scales with attacks."
    ),
}


# =============================================================================
# POWER RANKING SYSTEM
# =============================================================================

class PowerRankingSystem:
    """
    Comprehensive power ranking system for Slay the Spire elements.
    
    Uses Base Value (BV) metrics derived from community tier lists
    and mechanical analysis.
    """
    
    def __init__(self):
        """Initialize power ranking system with all data."""
        self.card_values: Dict[str, Dict[str, BaseValue]] = {
            'Ironclad': IRONCLAD_CARD_VALUES,
            'Silent': SILENT_CARD_VALUES,
            'Defect': DEFECT_CARD_VALUES,
            'Watcher': WATCHER_CARD_VALUES,
        }
        self.relic_values = RELIC_VALUES
    
    def get_card_value(self, card_name: str, character: str = None) -> Optional[BaseValue]:
        """
        Get the base value for a card.
        
        Args:
            card_name: Name of the card.
            character: Optional character to search (None = search all).
        
        Returns:
            BaseValue or None if not found.
        """
        # Clean card name (remove + for upgraded)
        clean_name = card_name.rstrip('+').strip()
        
        if character:
            values = self.card_values.get(character, {})
            return values.get(clean_name)
        
        # Search all characters
        for char_values in self.card_values.values():
            if clean_name in char_values:
                return char_values[clean_name]
        
        return None
    
    def get_relic_value(self, relic_name: str) -> Optional[BaseValue]:
        """Get the base value for a relic."""
        return self.relic_values.get(relic_name)
    
    def rank_cards(
        self,
        cards: List[str],
        character: str = None,
        context: Dict[str, Any] = None
    ) -> List[Tuple[str, float, str]]:
        """
        Rank a list of cards by adjusted value.
        
        Args:
            cards: List of card names.
            character: Character context.
            context: Optional context for synergy adjustments.
        
        Returns:
            List of (card_name, adjusted_score, reasoning) tuples,
            sorted by score descending.
        """
        results = []
        
        for card in cards:
            base_value = self.get_card_value(card, character)
            
            if base_value:
                score = base_value.score
                reason = f"[{base_value.tier.value}-Tier] {base_value.notes[:60]}..."
                
                # Apply context adjustments
                if context:
                    score = self._apply_context_adjustments(score, base_value, context)
                
                results.append((card, score, reason))
            else:
                results.append((card, 50.0, "Unknown card, default value"))
        
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def _apply_context_adjustments(
        self,
        score: float,
        base_value: BaseValue,
        context: Dict[str, Any]
    ) -> float:
        """Apply context-based adjustments to score."""
        adjusted = score
        
        # Synergy adjustment
        if 'deck_synergy' in context:
            synergy_factor = context['deck_synergy']
            adjusted += base_value.synergy_potential * synergy_factor * 20
        
        # Floor/act adjustment
        if 'floor' in context:
            floor = context['floor']
            act = (floor - 1) // 17 + 1
            
            # Late-game scaling cards are more valuable
            if ValueCategory.SCALING in base_value.categories and act >= 2:
                adjusted += 5
            
            # Early-game front-loaded damage is more valuable
            if ValueCategory.DAMAGE in base_value.categories and act == 1:
                if floor < 8:
                    adjusted += 3
        
        # HP-based adjustment for sustain
        if 'hp_percent' in context:
            hp_pct = context['hp_percent']
            if ValueCategory.SUSTAIN in base_value.categories and hp_pct < 0.5:
                adjusted += 10
        
        return min(100, max(0, adjusted))
    
    def get_tier_list(self, character: str) -> Dict[str, List[str]]:
        """
        Get a tier list for a character.
        
        Args:
            character: Character name.
        
        Returns:
            Dictionary of tier -> list of card names.
        """
        values = self.card_values.get(character, {})
        
        tier_list = {tier.value: [] for tier in PowerTier}
        
        for card_name, base_value in values.items():
            tier_list[base_value.tier.value].append(card_name)
        
        # Sort within each tier by score
        for tier in tier_list:
            tier_list[tier] = sorted(
                tier_list[tier],
                key=lambda c: values.get(c, BaseValue.from_score(0)).score,
                reverse=True
            )
        
        return tier_list
    
    def evaluate_card_pick(
        self,
        options: List[str],
        current_deck: List[str],
        character: str,
        floor: int = 1
    ) -> Dict[str, Any]:
        """
        Evaluate card pick options for a reward screen.
        
        Args:
            options: List of offered cards.
            current_deck: Current deck composition.
            character: Character name.
            floor: Current floor.
        
        Returns:
            Evaluation dictionary with recommendations.
        """
        from synergy_system import get_synergy_calculator
        
        synergy_calc = get_synergy_calculator()
        context = {'floor': floor}
        
        evaluations = []
        
        for card in options:
            base_value = self.get_card_value(card, character)
            
            if not base_value:
                evaluations.append({
                    'card': card,
                    'base_score': 50,
                    'synergy_delta': 0,
                    'final_score': 50,
                    'tier': 'C',
                    'recommendation': 'Unknown card'
                })
                continue
            
            # Calculate synergy delta
            synergy_delta = synergy_calc.evaluate_card_addition(current_deck, card)
            
            # Adjusted score
            synergy_bonus = min(15, synergy_delta * 5)
            final_score = base_value.score + synergy_bonus
            
            recommendation = "Skip" if final_score < 50 else \
                            "Consider" if final_score < 70 else \
                            "Take" if final_score < 85 else "Always Take"
            
            evaluations.append({
                'card': card,
                'base_score': base_value.score,
                'synergy_delta': synergy_delta,
                'synergy_bonus': synergy_bonus,
                'final_score': final_score,
                'tier': base_value.tier.value,
                'categories': [c.value for c in base_value.categories],
                'recommendation': recommendation,
                'notes': base_value.notes
            })
        
        # Add Skip option
        evaluations.append({
            'card': 'Skip',
            'base_score': 0,
            'synergy_delta': 0,
            'final_score': 40,  # Skip baseline
            'tier': 'N/A',
            'recommendation': 'Keep deck lean',
            'notes': 'Smaller decks are more consistent. Skip mediocre cards.'
        })
        
        # Sort by final score
        evaluations = sorted(evaluations, key=lambda x: x['final_score'], reverse=True)
        
        return {
            'evaluations': evaluations,
            'best_pick': evaluations[0]['card'],
            'skip_threshold': 50,
            'deck_size': len(current_deck),
            'deck_needs': self._analyze_deck_needs(current_deck, character)
        }
    
    def _analyze_deck_needs(self, deck: List[str], character: str) -> List[str]:
        """Analyze what the deck needs."""
        needs = []
        
        # Count categories in deck
        category_counts = {cat: 0 for cat in ValueCategory}
        
        for card in deck:
            bv = self.get_card_value(card, character)
            if bv:
                for cat in bv.categories:
                    category_counts[cat] += 1
        
        # Identify weaknesses
        if category_counts[ValueCategory.BLOCK] < 3:
            needs.append("More block/defense")
        if category_counts[ValueCategory.SCALING] < 2:
            needs.append("Scaling for long fights")
        if category_counts[ValueCategory.AOE] < 1:
            needs.append("AoE for multi-enemy fights")
        if category_counts[ValueCategory.DAMAGE] < 3:
            needs.append("More damage output")
        if category_counts[ValueCategory.DRAW] < 1:
            needs.append("Card draw for consistency")
        
        return needs if needs else ["Deck is well-rounded"]


# Global instance
_power_ranking: Optional[PowerRankingSystem] = None


def get_power_ranking() -> PowerRankingSystem:
    """Get the global power ranking system."""
    global _power_ranking
    if _power_ranking is None:
        _power_ranking = PowerRankingSystem()
    return _power_ranking


def get_card_tier(card_name: str, character: str = None) -> str:
    """Quick function to get a card's tier."""
    bv = get_power_ranking().get_card_value(card_name, character)
    return bv.tier.value if bv else "?"


def get_card_score(card_name: str, character: str = None) -> float:
    """Quick function to get a card's base score."""
    bv = get_power_ranking().get_card_value(card_name, character)
    return bv.score if bv else 50.0
