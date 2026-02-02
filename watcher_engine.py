"""
Watcher engine for Slay the Spire simulation.
Implements stance mechanics (Wrath, Calm, Divinity) and Mantra.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

from engine_common import (
    Card, CardType, PlayerState, EnemyState, DeckState, CombatResult,
    Intent, apply_damage_to_enemy, apply_damage_to_player,
    decrement_debuffs, create_starter_deck, get_playable_cards
)


# Watcher-specific cards
WATCHER_CARDS = {
    'Empty Fist': Card(
        name='Empty Fist',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 9, 'exit_stance': True}
    ),
    'Empty Body': Card(
        name='Empty Body',
        cost=1,
        card_type=CardType.SKILL,
        effects={'block': 7, 'exit_stance': True}
    ),
    'Flurry of Blows': Card(
        name='Flurry of Blows',
        cost=0,
        card_type=CardType.ATTACK,
        effects={'damage': 4, 'trigger_on_stance_change': True}
    ),
    'Crescendo': Card(
        name='Crescendo',
        cost=1,
        card_type=CardType.SKILL,
        effects={'enter_stance': 'wrath'},
        exhaust=True
    ),
    'Tranquility': Card(
        name='Tranquility',
        cost=1,
        card_type=CardType.SKILL,
        effects={'enter_stance': 'calm'},
        exhaust=True
    ),
    'Prostrate': Card(
        name='Prostrate',
        cost=0,
        card_type=CardType.SKILL,
        effects={'block': 4, 'mantra': 2}
    ),
    'Pray': Card(
        name='Pray',
        cost=1,
        card_type=CardType.SKILL,
        effects={'mantra': 3, 'retain': True}
    ),
    'Tantrum': Card(
        name='Tantrum',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 3, 'hits': 3, 'enter_stance': 'wrath'}
    ),
    'Conclude': Card(
        name='Conclude',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 12, 'end_turn': True}
    ),
    'Fear No Evil': Card(
        name='Fear No Evil',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 8, 'enter_stance_if_attacked': 'calm'}
    ),
    'Mental Fortress': Card(
        name='Mental Fortress',
        cost=1,
        card_type=CardType.POWER,
        effects={'block_on_stance_change': 4}
    ),
}


@dataclass
class WatcherState(PlayerState):
    """Extended player state for Watcher with stance and mantra tracking."""
    mantra: int = 0
    mental_fortress_stacks: int = 0
    retain_cards: List[Card] = field(default_factory=list)


def create_watcher_player(relic: str = 'none') -> WatcherState:
    """Create Watcher player state."""
    player = WatcherState(
        hp=72,
        max_hp=72,
        energy=3,
        max_energy=3,
        stance='neutral',
        relics=[relic] if relic != 'none' else []
    )
    
    # Pure Water relic: add Miracle to hand at start of combat
    # (simplified here)
    
    return player


def enter_stance(player: WatcherState, new_stance: str) -> None:
    """
    Enter a new stance.
    
    Args:
        player: Player state.
        new_stance: Target stance.
    """
    old_stance = player.stance
    
    if old_stance == new_stance:
        return  # No change
    
    # Exit old stance effects
    if old_stance == 'calm':
        player.energy += 2  # Gain 2 energy when leaving Calm
    
    # Enter new stance
    player.stance = new_stance
    
    # Mental Fortress trigger
    if player.mental_fortress_stacks > 0:
        player.block += player.mental_fortress_stacks


def exit_stance(player: WatcherState) -> None:
    """Exit current stance to neutral."""
    enter_stance(player, 'neutral')


def add_mantra(player: WatcherState, amount: int) -> None:
    """
    Add mantra to player.
    
    Args:
        player: Player state.
        amount: Mantra to add.
    """
    player.mantra += amount
    
    # Check for Divinity
    if player.mantra >= 10:
        player.mantra -= 10
        enter_stance(player, 'divinity')


def get_damage_multiplier(stance: str) -> float:
    """Get damage multiplier for current stance."""
    if stance == 'wrath':
        return 2.0
    elif stance == 'divinity':
        return 3.0
    return 1.0


def get_damage_taken_multiplier(stance: str) -> float:
    """Get damage taken multiplier for current stance."""
    if stance == 'wrath':
        return 2.0
    return 1.0


def get_enemy_intent(enemy: EnemyState, rng: np.random.Generator, turn: int) -> Tuple[Intent, int]:
    """Generate enemy intent."""
    roll = rng.random()
    
    if turn == 1:
        return Intent.ATTACK, enemy.strength + 9
    elif roll < 0.5:
        attack_damage = 7 + enemy.strength + (turn // 3) * 2
        return Intent.ATTACK, attack_damage
    elif roll < 0.7:
        return Intent.BUFF, 2
    else:
        return Intent.DEFEND, 10


def evaluate_card_value(
    card: Card,
    player: WatcherState,
    enemy: EnemyState,
    deck_state: DeckState
) -> float:
    """Evaluate the value of playing a card."""
    value = 0.0
    effects = card.effects
    
    damage_mult = get_damage_multiplier(player.stance)
    
    # Damage
    if 'damage' in effects:
        base_damage = effects['damage'] + player.strength
        hits = effects.get('hits', 1)
        total_damage = base_damage * hits * damage_mult
        if enemy.vulnerable > 0:
            total_damage = int(total_damage * 1.5)
        value += min(total_damage, enemy.hp) * 0.9
    
    # Block
    if 'block' in effects:
        block_amount = effects['block'] + player.dexterity
        if enemy.intent == Intent.ATTACK:
            incoming = enemy.intent_value * get_damage_taken_multiplier(player.stance)
            value += min(block_amount, incoming) * 1.3
        else:
            value += block_amount * 0.3
    
    # Stance changes
    if 'enter_stance' in effects:
        target_stance = effects['enter_stance']
        if target_stance == 'wrath':
            if enemy.intent != Intent.ATTACK or player.block >= enemy.intent_value * 2:
                value += 15  # Good if safe
            else:
                value -= 10  # Risky
        elif target_stance == 'calm':
            value += 8  # Energy gain on exit
    
    if effects.get('exit_stance') and player.stance == 'calm':
        value += 10  # Gain energy
    
    # Mantra
    if 'mantra' in effects:
        mantra_to_divinity = 10 - player.mantra
        if effects['mantra'] >= mantra_to_divinity:
            value += 30  # About to hit Divinity
        else:
            value += effects['mantra'] * 2
    
    # Mental Fortress
    if effects.get('block_on_stance_change'):
        value += effects['block_on_stance_change'] * 5
    
    # End turn penalty
    if effects.get('end_turn'):
        value -= 20
    
    if card.cost > 0:
        value /= card.cost
    
    return value


def select_card_to_play(
    deck_state: DeckState,
    player: WatcherState,
    enemy: EnemyState
) -> Optional[Card]:
    """Select the best card to play."""
    playable = get_playable_cards(deck_state, player)
    
    if not playable:
        return None
    
    best_card = None
    best_value = -float('inf')
    
    for card in playable:
        value = evaluate_card_value(card, player, enemy, deck_state)
        if value > best_value:
            best_value = value
            best_card = card
    
    return best_card if best_value > 0 else None


def play_card(
    card: Card,
    player: WatcherState,
    enemy: EnemyState,
    deck_state: DeckState,
    rng: np.random.Generator
) -> bool:
    """
    Execute the effects of playing a card.
    
    Returns:
        True if turn should end.
    """
    player.energy -= card.cost
    effects = card.effects
    damage_mult = get_damage_multiplier(player.stance)
    
    # Damage
    if 'damage' in effects:
        base_damage = effects['damage'] + player.strength
        hits = effects.get('hits', 1)
        
        for _ in range(hits):
            total_damage = int(base_damage * damage_mult)
            if enemy.vulnerable > 0:
                total_damage = int(total_damage * 1.5)
            
            if enemy.block >= total_damage:
                enemy.block -= total_damage
            else:
                actual_damage = total_damage - enemy.block
                enemy.block = 0
                enemy.hp -= actual_damage
    
    # Block
    if 'block' in effects:
        player.block += effects['block'] + player.dexterity
    
    # Stance changes
    if 'enter_stance' in effects:
        enter_stance(player, effects['enter_stance'])
    
    if effects.get('exit_stance'):
        exit_stance(player)
    
    # Mantra
    if 'mantra' in effects:
        add_mantra(player, effects['mantra'])
    
    # Mental Fortress
    if effects.get('block_on_stance_change'):
        player.mental_fortress_stacks += effects['block_on_stance_change']
    
    # Handle card destination
    if card.exhaust:
        deck_state.exhaust_card(card)
    else:
        deck_state.discard_card(card)
    
    return effects.get('end_turn', False)


def simulate_combat(
    player: WatcherState,
    enemy: EnemyState,
    deck: List[Card],
    rng: np.random.Generator,
    max_turns: int = 50
) -> CombatResult:
    """Simulate a full combat encounter."""
    deck_state = DeckState(draw_pile=[c.copy() for c in deck])
    deck_state.shuffle_draw_pile(rng)
    
    result = CombatResult()
    starting_hp = player.hp
    
    for turn in range(1, max_turns + 1):
        result.turns = turn
        
        # Start of turn
        player.block = 0
        
        # Divinity gives 3 energy, otherwise normal
        if player.stance == 'divinity':
            player.energy = player.max_energy + 3
            # Exit Divinity after granting bonus energy (per game rules)
            enter_stance(player, 'neutral')
        else:
            player.energy = player.max_energy
        
        deck_state.draw_cards(5, rng)
        
        enemy.intent, enemy.intent_value = get_enemy_intent(enemy, rng, turn)
        
        # Play cards
        while player.energy > 0 or any(c.cost == 0 for c in deck_state.hand):
            card = select_card_to_play(deck_state, player, enemy)
            if card is None:
                break
            
            end_turn = play_card(card, player, enemy, deck_state, rng)
            result.cards_played += 1
            
            if enemy.hp <= 0:
                result.win = True
                result.final_hp = player.hp
                result.enemy_hp = enemy.hp
                result.damage_taken = starting_hp - player.hp
                return result
            
            if end_turn:
                break
        
        deck_state.discard_hand()
        
        # Enemy turn
        damage_taken_mult = get_damage_taken_multiplier(player.stance)
        
        if enemy.intent == Intent.ATTACK:
            adjusted_damage = int(enemy.intent_value * damage_taken_mult)
            apply_damage_to_player(player, adjusted_damage, enemy)
        elif enemy.intent == Intent.BUFF:
            enemy.strength += enemy.intent_value
        elif enemy.intent == Intent.DEFEND:
            enemy.block += enemy.intent_value
        
        decrement_debuffs(enemy)
        
        if player.hp <= 0:
            result.win = False
            result.final_hp = 0
            result.enemy_hp = enemy.hp
            result.damage_taken = starting_hp
            return result
    
    result.win = False
    result.final_hp = player.hp
    result.enemy_hp = enemy.hp
    result.damage_taken = starting_hp - player.hp
    return result


def simulate_run(
    rng: np.random.Generator,
    relic: str = 'none',
    enemy_hp: int = 105,
    max_turns: int = 50
) -> CombatResult:
    """Simulate a single Watcher run."""
    player = create_watcher_player(relic)
    enemy = EnemyState(name="Act1Elite", hp=enemy_hp, max_hp=enemy_hp)
    deck = create_starter_deck('Watcher')
    
    return simulate_combat(player, enemy, deck, rng, max_turns)
