"""
Relic effect system for Slay the Spire simulation.

Implements relic hooks for combat lifecycle events.
Resolution for G2: Relic effects not modeled.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from engine_common import PlayerState, EnemyState, DeckState, Card


class RelicTrigger(Enum):
    """When relic effects trigger."""
    COMBAT_START = "combat_start"
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    CARD_PLAYED = "card_played"
    CARD_DRAWN = "card_drawn"
    DAMAGE_DEALT = "damage_dealt"
    DAMAGE_TAKEN = "damage_taken"
    BLOCK_GAINED = "block_gained"
    ENEMY_KILLED = "enemy_killed"
    COMBAT_END = "combat_end"
    SHUFFLE = "shuffle"
    EXHAUST = "exhaust"
    HEAL = "heal"


@dataclass
class RelicEffect:
    """
    A single relic effect.
    
    Attributes:
        trigger: When this effect triggers.
        effect_type: Type of effect (heal, block, damage, draw, strength, etc.).
        value: Numeric value for the effect.
        condition: Condition for effect to apply (e.g., "first_attack", "hp_below_50").
        counter_max: If effect requires counter (e.g., Nunchaku = 10 attacks).
        target: Target of effect (self, enemy, all_enemies).
    """
    trigger: RelicTrigger
    effect_type: str
    value: int = 0
    condition: str = ""
    counter_max: int = 0
    target: str = "self"


@dataclass
class Relic:
    """
    A relic with its effects.
    
    Attributes:
        name: Relic name.
        rarity: Relic rarity (Starter, Common, Uncommon, Rare, Boss, Shop, Event).
        character: Character-specific relic (empty for universal).
        description: Relic description.
        effects: List of relic effects.
        counter: Current counter value for counter-based effects.
        active: Whether the relic is currently active.
    """
    name: str
    rarity: str
    character: str = ""
    description: str = ""
    effects: List[RelicEffect] = field(default_factory=list)
    counter: int = 0
    active: bool = True


class RelicManager:
    """
    Manages relic effects during combat.
    
    Provides hooks for combat lifecycle events.
    """
    
    def __init__(self):
        """Initialize relic manager."""
        self.relics: List[Relic] = []
        self._definitions: Dict[str, Dict] = {}
        self._loaded = False
    
    def load_definitions(self, path: str = "data/relics/relics.json") -> None:
        """Load relic definitions from JSON."""
        if self._loaded:
            return
        
        filepath = Path(path)
        if not filepath.exists():
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Flatten all relic categories
        for category in ['starter_relics', 'common_relics', 'uncommon_relics', 
                         'rare_relics', 'boss_relics', 'shop_relics']:
            if category in data:
                for name, relic_data in data[category].items():
                    self._definitions[name.lower()] = {
                        'name': name,
                        'rarity': relic_data.get('rarity', 'Common'),
                        'character': relic_data.get('character', ''),
                        'description': relic_data.get('description', ''),
                        'effects': relic_data.get('effects', {})
                    }
        
        self._loaded = True
    
    def _create_relic_effects(self, effects_dict: Dict) -> List[RelicEffect]:
        """Create RelicEffect list from effects dictionary."""
        effects = []
        
        # Combat start effects
        if 'block_start_combat' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_START,
                effect_type='block',
                value=effects_dict['block_start_combat']
            ))
        
        if 'vulnerable_start_combat' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_START,
                effect_type='vulnerable',
                value=effects_dict['vulnerable_start_combat'],
                target='all_enemies'
            ))
        
        if 'draw_start_combat' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_START,
                effect_type='draw',
                value=effects_dict['draw_start_combat']
            ))
        
        if 'heal_start_combat' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_START,
                effect_type='heal',
                value=effects_dict['heal_start_combat']
            ))
        
        if 'artifact_start_combat' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_START,
                effect_type='artifact',
                value=effects_dict['artifact_start_combat']
            ))
        
        if 'channel_start_combat' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_START,
                effect_type='channel',
                value=1,
                target=effects_dict['channel_start_combat']
            ))
        
        # Turn start effects
        if 'energy_turn_1' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_START,
                effect_type='energy',
                value=effects_dict['energy_turn_1'],
                condition='turn_1'
            ))
        
        if 'draw_turn_1_bonus' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_START,
                effect_type='draw',
                value=effects_dict['draw_turn_1_bonus'],
                condition='turn_1'
            ))
        
        if 'block_turn_2' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_START,
                effect_type='block',
                value=effects_dict['block_turn_2'],
                condition='turn_2'
            ))
        
        if 'block_turn_3' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_START,
                effect_type='block',
                value=effects_dict['block_turn_3'],
                condition='turn_3'
            ))
        
        if 'draw_per_turn' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_START,
                effect_type='draw',
                value=effects_dict['draw_per_turn']
            ))
        
        if 'energy_per_turn' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_START,
                effect_type='energy',
                value=effects_dict['energy_per_turn']
            ))
        
        if 'damage_start_turn' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_START,
                effect_type='damage',
                value=effects_dict['damage_start_turn'],
                target='all_enemies'
            ))
        
        # Turn end effects
        if 'block_end_of_turn' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_END,
                effect_type='block',
                value=effects_dict['block_end_of_turn']
            ))
        
        if 'block_if_no_block' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_END,
                effect_type='block',
                value=effects_dict['block_if_no_block'],
                condition='no_block'
            ))
        
        # Combat end effects
        if 'heal_end_combat' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_END,
                effect_type='heal',
                value=effects_dict['heal_end_combat']
            ))
        
        # Card played effects
        if 'first_attack_bonus' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.CARD_PLAYED,
                effect_type='damage_bonus',
                value=effects_dict['first_attack_bonus'],
                condition='first_attack'
            ))
        
        if 'energy_per_10_attacks' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.CARD_PLAYED,
                effect_type='energy',
                value=1,
                counter_max=10,
                condition='attack_played'
            ))
        
        if 'strength_per_3_attacks' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.CARD_PLAYED,
                effect_type='strength',
                value=effects_dict['strength_per_3_attacks'],
                counter_max=3,
                condition='attack_played'
            ))
        
        if 'dexterity_per_3_attacks' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.CARD_PLAYED,
                effect_type='dexterity',
                value=effects_dict['dexterity_per_3_attacks'],
                counter_max=3,
                condition='attack_played'
            ))
        
        if 'block_per_3_attacks' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.CARD_PLAYED,
                effect_type='block',
                value=effects_dict['block_per_3_attacks'],
                counter_max=3,
                condition='attack_played'
            ))
        
        if 'heal_on_power' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.CARD_PLAYED,
                effect_type='heal',
                value=effects_dict['heal_on_power'],
                condition='power_played'
            ))
        
        # Damage dealt effects
        if 'double_damage_every_10' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.DAMAGE_DEALT,
                effect_type='damage_double',
                value=1,
                counter_max=10
            ))
        
        # Damage taken effects
        if 'thorns' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.DAMAGE_TAKEN,
                effect_type='damage',
                value=effects_dict['thorns'],
                target='attacker'
            ))
        
        if 'draw_on_hp_loss' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.DAMAGE_TAKEN,
                effect_type='draw',
                value=effects_dict['draw_on_hp_loss']
            ))
        
        if 'draw_on_first_hp_loss' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.DAMAGE_TAKEN,
                effect_type='draw',
                value=effects_dict['draw_on_first_hp_loss'],
                condition='first_damage'
            ))
        
        # Block gained effects
        if 'damage_on_block' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.BLOCK_GAINED,
                effect_type='damage',
                value=effects_dict['damage_on_block'],
                target='random_enemy'
            ))
        
        # Enemy killed effects
        if 'energy_on_kill' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.ENEMY_KILLED,
                effect_type='energy',
                value=effects_dict['energy_on_kill']
            ))
        
        if 'draw_on_kill' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.ENEMY_KILLED,
                effect_type='draw',
                value=effects_dict['draw_on_kill']
            ))
        
        # Shuffle effects
        if 'block_on_shuffle' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.SHUFFLE,
                effect_type='block',
                value=effects_dict['block_on_shuffle']
            ))
        
        if 'energy_per_3_shuffles' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.SHUFFLE,
                effect_type='energy',
                value=effects_dict['energy_per_3_shuffles'],
                counter_max=3
            ))
        
        # Exhaust effects
        if 'add_card_on_exhaust' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.EXHAUST,
                effect_type='add_random_card',
                value=1
            ))
        
        if 'block_on_exhaust' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.EXHAUST,
                effect_type='block',
                value=effects_dict['block_on_exhaust']
            ))
        
        if 'draw_on_exhaust' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.EXHAUST,
                effect_type='draw',
                value=effects_dict['draw_on_exhaust']
            ))
        
        # Passive stat effects (applied at combat start)
        if 'strength' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_START,
                effect_type='strength',
                value=effects_dict['strength']
            ))
        
        if 'dexterity' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.COMBAT_START,
                effect_type='dexterity',
                value=effects_dict['dexterity']
            ))
        
        if 'energy' in effects_dict:
            effects.append(RelicEffect(
                trigger=RelicTrigger.TURN_START,
                effect_type='energy',
                value=effects_dict['energy']
            ))
        
        return effects
    
    def add_relic(self, name: str) -> Optional[Relic]:
        """
        Add a relic by name.
        
        Args:
            name: Relic name.
        
        Returns:
            The added Relic, or None if not found.
        """
        self.load_definitions()
        
        relic_data = self._definitions.get(name.lower())
        if not relic_data:
            # Handle common name variations
            for key, data in self._definitions.items():
                if data['name'].lower() == name.lower():
                    relic_data = data
                    break
        
        if not relic_data:
            return None
        
        effects = self._create_relic_effects(relic_data.get('effects', {}))
        
        relic = Relic(
            name=relic_data['name'],
            rarity=relic_data['rarity'],
            character=relic_data.get('character', ''),
            description=relic_data.get('description', ''),
            effects=effects
        )
        
        self.relics.append(relic)
        return relic
    
    def add_relics_from_player(self, player: PlayerState) -> None:
        """Add relics from player state."""
        for relic_name in player.relics:
            self.add_relic(relic_name)
    
    def trigger(
        self,
        trigger_type: RelicTrigger,
        player: PlayerState,
        enemy: Optional[EnemyState] = None,
        deck_state: Optional[DeckState] = None,
        card: Optional[Card] = None,
        turn: int = 0,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Trigger relic effects for an event.
        
        Args:
            trigger_type: Type of trigger.
            player: Player state.
            enemy: Optional enemy state.
            deck_state: Optional deck state.
            card: Optional card that triggered the event.
            turn: Current turn number.
            context: Optional additional context.
        
        Returns:
            Dictionary of effects that were applied.
        """
        if context is None:
            context = {}
        
        applied_effects: Dict[str, Any] = {
            'block': 0,
            'damage': 0,
            'heal': 0,
            'draw': 0,
            'energy': 0,
            'strength': 0,
            'dexterity': 0,
            'vulnerable': 0,
            'weak': 0,
            'artifact': 0,
            'damage_bonus': 0,
            'cards_added': []
        }
        
        for relic in self.relics:
            if not relic.active:
                continue
            
            for effect in relic.effects:
                if effect.trigger != trigger_type:
                    continue
                
                # Check conditions
                if not self._check_condition(effect.condition, player, enemy, card, turn, context, relic):
                    continue
                
                # Handle counter-based effects
                if effect.counter_max > 0:
                    relic.counter += 1
                    if relic.counter < effect.counter_max:
                        continue
                    relic.counter = 0
                
                # Apply effect
                self._apply_effect(effect, player, enemy, deck_state, applied_effects)
        
        return applied_effects
    
    def _check_condition(
        self,
        condition: str,
        player: PlayerState,
        enemy: Optional[EnemyState],
        card: Optional[Card],
        turn: int,
        context: Dict,
        relic: Relic
    ) -> bool:
        """Check if a condition is met."""
        if not condition:
            return True
        
        if condition == 'turn_1':
            return turn == 1
        elif condition == 'turn_2':
            return turn == 2
        elif condition == 'turn_3':
            return turn == 3
        elif condition == 'no_block':
            return player.block == 0
        elif condition == 'first_attack':
            return context.get('first_attack', False)
        elif condition == 'attack_played':
            from engine_common import CardType
            return card is not None and card.card_type == CardType.ATTACK
        elif condition == 'power_played':
            from engine_common import CardType
            return card is not None and card.card_type == CardType.POWER
        elif condition == 'skill_played':
            from engine_common import CardType
            return card is not None and card.card_type == CardType.SKILL
        elif condition == 'first_damage':
            return context.get('first_damage', False)
        elif condition == 'hp_below_50':
            return player.hp <= player.max_hp / 2
        
        return True
    
    def _apply_effect(
        self,
        effect: RelicEffect,
        player: PlayerState,
        enemy: Optional[EnemyState],
        deck_state: Optional[DeckState],
        applied_effects: Dict
    ) -> None:
        """Apply a single effect."""
        if effect.effect_type == 'block':
            player.block += effect.value
            applied_effects['block'] += effect.value
        
        elif effect.effect_type == 'damage' and enemy:
            if enemy.block >= effect.value:
                enemy.block -= effect.value
            else:
                actual_damage = effect.value - enemy.block
                enemy.block = 0
                enemy.hp -= actual_damage
                applied_effects['damage'] += actual_damage
        
        elif effect.effect_type == 'heal':
            heal_amount = min(effect.value, player.max_hp - player.hp)
            player.hp += heal_amount
            applied_effects['heal'] += heal_amount
        
        elif effect.effect_type == 'draw' and deck_state:
            # Just record the draw amount, actual draw happens in engine
            applied_effects['draw'] += effect.value
        
        elif effect.effect_type == 'energy':
            player.energy += effect.value
            applied_effects['energy'] += effect.value
        
        elif effect.effect_type == 'strength':
            player.strength += effect.value
            applied_effects['strength'] += effect.value
        
        elif effect.effect_type == 'dexterity':
            player.dexterity += effect.value
            applied_effects['dexterity'] += effect.value
        
        elif effect.effect_type == 'vulnerable' and enemy:
            enemy.vulnerable += effect.value
            applied_effects['vulnerable'] += effect.value
        
        elif effect.effect_type == 'weak' and enemy:
            enemy.weak += effect.value
            applied_effects['weak'] += effect.value
        
        elif effect.effect_type == 'artifact':
            player.artifact += effect.value
            applied_effects['artifact'] += effect.value
        
        elif effect.effect_type == 'damage_bonus':
            applied_effects['damage_bonus'] += effect.value
    
    def reset_combat(self) -> None:
        """Reset combat-specific state for all relics."""
        for relic in self.relics:
            relic.counter = 0
            relic.active = True
    
    def clear(self) -> None:
        """Remove all relics."""
        self.relics = []


# Global relic manager instance
_relic_manager: Optional[RelicManager] = None


def get_relic_manager() -> RelicManager:
    """Get the global relic manager instance."""
    global _relic_manager
    if _relic_manager is None:
        _relic_manager = RelicManager()
    return _relic_manager


def create_relic_manager() -> RelicManager:
    """Create a new relic manager instance."""
    return RelicManager()
