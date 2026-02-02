"""
Silent engine for Slay the Spire simulation.
Implements poison mechanics, discard synergies, and shiv generation.

Reference: turn0browsertab1 for Silent starting deck and strategy.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

from engine_common import (
    Card, CardType, PlayerState, EnemyState, DeckState, CombatResult,
    Intent, apply_damage_to_enemy, apply_damage_to_player,
    apply_debuff, apply_poison, process_poison_tick, decrement_debuffs,
    create_starter_deck, get_playable_cards
)

# =========================================================================
# EVALUATION CONSTANTS
# Configurable parameters for card evaluation heuristics
# =========================================================================

# Average enemy attack damage used for estimating weak value
AVG_ENEMY_ATTACK_DAMAGE = 10

# Weak reduces incoming damage by this fraction
WEAK_DAMAGE_REDUCTION = 0.25

# Poison value multiplier (applied after triangular sum calculation)
POISON_VALUE_MULTIPLIER = 0.9

# HP divisor for estimating remaining turns
TURNS_PER_HP_DIVISOR = 15


# Silent-specific cards
SILENT_CARDS = {
    'Deadly Poison': Card(
        name='Deadly Poison',
        cost=1,
        card_type=CardType.SKILL,
        effects={'poison': 5}
    ),
    'Bouncing Flask': Card(
        name='Bouncing Flask',
        cost=2,
        card_type=CardType.SKILL,
        effects={'poison': 3, 'hits': 3}
    ),
    'Catalyst': Card(
        name='Catalyst',
        cost=1,
        card_type=CardType.SKILL,
        effects={'double_poison': True},
        exhaust=True
    ),
    'Noxious Fumes': Card(
        name='Noxious Fumes',
        cost=1,
        card_type=CardType.POWER,
        effects={'poison_per_turn': 2}
    ),
    'Blade Dance': Card(
        name='Blade Dance',
        cost=1,
        card_type=CardType.SKILL,
        effects={'add_shivs': 3}
    ),
    'Acrobatics': Card(
        name='Acrobatics',
        cost=1,
        card_type=CardType.SKILL,
        effects={'draw': 3, 'discard': 1}
    ),
    'Prepared': Card(
        name='Prepared',
        cost=0,
        card_type=CardType.SKILL,
        effects={'draw': 1, 'discard': 1}
    ),
    'Backflip': Card(
        name='Backflip',
        cost=1,
        card_type=CardType.SKILL,
        effects={'block': 5, 'draw': 2}
    ),
    'Dash': Card(
        name='Dash',
        cost=2,
        card_type=CardType.ATTACK,
        effects={'damage': 10, 'block': 10}
    ),
    'Predator': Card(
        name='Predator',
        cost=2,
        card_type=CardType.ATTACK,
        effects={'damage': 15, 'draw_next_turn': 2}
    ),
    'Shiv': Card(
        name='Shiv',
        cost=0,
        card_type=CardType.ATTACK,
        effects={'damage': 4},
        exhaust=True
    ),
}


@dataclass
class SilentState(PlayerState):
    """Extended player state for Silent with poison tracking."""
    noxious_fumes_stacks: int = 0
    draw_next_turn: int = 0


def create_silent_player(relic: str = 'none') -> SilentState:
    """
    Create Silent player state with starting stats.
    
    Args:
        relic: Starting relic name.
    
    Returns:
        SilentState configured for Silent.
    """
    player = SilentState(
        hp=70,
        max_hp=70,
        energy=3,
        max_energy=3,
        relics=['Ring of the Snake'] if relic == 'none' else [relic, 'Ring of the Snake']
    )
    
    # Ring of the Snake: draw 2 extra cards on first turn
    # (handled in combat simulation)
    
    if relic == 'snecko_eye':
        player.max_energy = 2
        player.energy = 2
    
    return player


def get_enemy_intent(enemy: EnemyState, rng: np.random.Generator, turn: int) -> Tuple[Intent, int]:
    """
    Generate enemy intent for the current turn.
    
    Based on Act 1 Elite patterns, damage is calibrated to create 
    realistic win rates of 40-70% for starter decks.
    
    Args:
        enemy: Enemy state.
        rng: Random number generator.
        turn: Current turn number.
    
    Returns:
        Tuple of (Intent, value).
    """
    roll = rng.random()
    
    if turn == 1:
        # Strong opening attack
        return Intent.ATTACK, enemy.strength + 16
    elif roll < 0.6:
        # After turn 1: 60% chance to attack with scaling damage
        attack_damage = 12 + enemy.strength + (turn // 2) * 3
        return Intent.ATTACK, attack_damage
    elif roll < 0.75:
        # After turn 1: 15% chance to buff
        return Intent.BUFF, 3
    elif roll < 0.88:
        # After turn 1: 13% chance to debuff
        return Intent.DEBUFF, 2
    else:
        # After turn 1: 12% chance to defend
        return Intent.DEFEND, 10


def evaluate_card_value(
    card: Card,
    player: SilentState,
    enemy: EnemyState,
    deck_state: DeckState
) -> float:
    """
    Evaluate the value of playing a card.
    
    Args:
        card: Card to evaluate.
        player: Player state.
        enemy: Enemy state.
        deck_state: Deck state.
    
    Returns:
        Estimated value of playing the card.
    """
    value = 0.0
    effects = card.effects
    
    # Damage value
    if 'damage' in effects:
        base_damage = effects['damage'] + player.strength
        if enemy.vulnerable > 0:
            base_damage = int(base_damage * 1.5)
        value += min(base_damage, enemy.hp) * 0.8
    
    # Block value
    if 'block' in effects:
        block_amount = effects['block'] + player.dexterity
        if enemy.intent == Intent.ATTACK:
            value += min(block_amount, enemy.intent_value) * 1.3
        else:
            value += block_amount * 0.2
    
    # Poison value (long-term damage)
    if 'poison' in effects:
        poison_amount = effects['poison']
        if 'hits' in effects:
            poison_amount *= effects['hits']
        
        # Calculate incremental poison damage using triangular number formula
        current_poison = enemy.poison
        new_total = current_poison + poison_amount
        # Total damage from poison n = n*(n+1)/2 (triangular number)
        damage_with_new = new_total * (new_total + 1) / 2
        damage_without_new = current_poison * (current_poison + 1) / 2
        incremental_damage = damage_with_new - damage_without_new
        value += min(incremental_damage, enemy.hp) * POISON_VALUE_MULTIPLIER
    
    # Double/Triple poison (Catalyst - triples when upgraded)
    if effects.get('double_poison') or effects.get('triple_poison'):
        if enemy.poison > 0:
            current = enemy.poison
            # Catalyst doubles (or triples if upgraded)
            multiplier = 3 if effects.get('triple_poison') else 2
            new_poison = current * multiplier
            # Calculate value of the multiplication
            damage_new = new_poison * (new_poison + 1) / 2
            damage_old = current * (current + 1) / 2
            incremental = min(damage_new - damage_old, enemy.hp)
            value += incremental * POISON_VALUE_MULTIPLIER
    
    # Noxious Fumes (poison per turn)
    if 'poison_per_turn' in effects:
        turns_remaining = max(1, enemy.hp // TURNS_PER_HP_DIVISOR)
        # Each turn adds poison_per_turn, which then deals damage
        # Over n turns: sum of (1 + 2 + ... + n*poison_per_turn) roughly
        ppt = effects['poison_per_turn']
        total_fumes_damage = sum(i * ppt for i in range(1, turns_remaining + 1))
        value += min(total_fumes_damage, enemy.hp) * 0.7
    
    # Draw value
    if 'draw' in effects:
        value += effects['draw'] * 3
    
    # Shivs
    if 'add_shivs' in effects:
        shiv_damage = effects['add_shivs'] * (4 + player.strength)
        if enemy.vulnerable > 0:
            shiv_damage = int(shiv_damage * 1.5)
        value += shiv_damage * 0.7
    
    # Weak
    if 'weak' in effects:
        # Weak reduces incoming damage by WEAK_DAMAGE_REDUCTION for its duration
        # Value = effective_turns * avg_damage * reduction_fraction
        turns_remaining = max(1, enemy.hp // TURNS_PER_HP_DIVISOR)
        effective_duration = min(effects['weak'], turns_remaining)
        weak_value = effective_duration * AVG_ENEMY_ATTACK_DAMAGE * WEAK_DAMAGE_REDUCTION
        value += weak_value
    
    # Energy efficiency
    if card.cost > 0:
        value /= card.cost
    
    return value


def select_card_to_play(
    deck_state: DeckState,
    player: SilentState,
    enemy: EnemyState
) -> Optional[Card]:
    """
    Select the best card to play from hand.
    
    Args:
        deck_state: Current deck state.
        player: Player state.
        enemy: Enemy state.
    
    Returns:
        Best card to play, or None if no card should be played.
    """
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
    player: SilentState,
    enemy: EnemyState,
    deck_state: DeckState,
    rng: np.random.Generator
) -> None:
    """
    Execute the effects of playing a card.
    
    Args:
        card: Card to play.
        player: Player state.
        enemy: Enemy state.
        deck_state: Deck state.
        rng: Random number generator.
    """
    player.energy -= card.cost
    effects = card.effects
    
    # Damage
    if 'damage' in effects:
        base_damage = effects['damage'] + player.strength
        if enemy.vulnerable > 0:
            base_damage = int(base_damage * 1.5)
        
        if enemy.block >= base_damage:
            enemy.block -= base_damage
        else:
            actual_damage = base_damage - enemy.block
            enemy.block = 0
            enemy.hp -= actual_damage
    
    # Block
    if 'block' in effects:
        player.block += effects['block'] + player.dexterity
    
    # Poison
    if 'poison' in effects:
        hits = effects.get('hits', 1)
        for _ in range(hits):
            apply_poison(enemy, effects['poison'])
    
    # Double poison
    if effects.get('double_poison'):
        enemy.poison *= 2
    
    # Noxious Fumes
    if 'poison_per_turn' in effects:
        player.noxious_fumes_stacks += effects['poison_per_turn']
    
    # Weak
    if 'weak' in effects:
        apply_debuff(enemy, 'weak', effects['weak'])
    
    # Draw
    if 'draw' in effects:
        deck_state.draw_cards(effects['draw'], rng)
    
    # Discard (for Acrobatics, Survivor, etc.)
    if 'discard' in effects:
        discard_count = effects['discard']
        # Discard lowest value cards
        for _ in range(discard_count):
            if deck_state.hand:
                # Simple: discard first non-essential card
                for c in deck_state.hand:
                    if c.name not in ['Catalyst', 'Noxious Fumes']:
                        deck_state.discard_card(c)
                        break
    
    # Add shivs
    if 'add_shivs' in effects:
        for _ in range(effects['add_shivs']):
            shiv = SILENT_CARDS['Shiv'].copy()
            deck_state.hand.append(shiv)
    
    # Draw next turn
    if 'draw_next_turn' in effects:
        player.draw_next_turn += effects['draw_next_turn']
    
    # Handle card destination
    if card.exhaust:
        deck_state.exhaust_card(card)
    else:
        deck_state.discard_card(card)


def simulate_combat(
    player: SilentState,
    enemy: EnemyState,
    deck: List[Card],
    rng: np.random.Generator,
    max_turns: int = 50
) -> CombatResult:
    """
    Simulate a full combat encounter.
    
    Args:
        player: Initial player state.
        enemy: Initial enemy state.
        deck: Starting deck.
        rng: Random number generator.
        max_turns: Maximum turns before timeout.
    
    Returns:
        CombatResult with outcome statistics.
    """
    deck_state = DeckState(draw_pile=[c.copy() for c in deck])
    deck_state.shuffle_draw_pile(rng)
    
    result = CombatResult()
    starting_hp = player.hp
    peak_poison = 0
    
    for turn in range(1, max_turns + 1):
        result.turns = turn
        
        # Start of turn
        player.block = 0
        player.energy = player.max_energy
        
        # Apply Noxious Fumes
        if player.noxious_fumes_stacks > 0:
            apply_poison(enemy, player.noxious_fumes_stacks)
        
        # Draw cards
        base_draw = 5
        if turn == 1 and 'Ring of the Snake' in player.relics:
            base_draw += 2  # Ring of the Snake bonus
        if player.draw_next_turn > 0:
            base_draw += player.draw_next_turn
            player.draw_next_turn = 0
        
        deck_state.draw_cards(base_draw, rng)
        
        # Get enemy intent
        enemy.intent, enemy.intent_value = get_enemy_intent(enemy, rng, turn)
        
        # Play cards
        while player.energy > 0 or any(c.cost == 0 for c in deck_state.hand):
            card = select_card_to_play(deck_state, player, enemy)
            if card is None:
                break
            play_card(card, player, enemy, deck_state, rng)
            result.cards_played += 1
            
            # Track peak poison
            if enemy.poison > peak_poison:
                peak_poison = enemy.poison
            
            if enemy.hp <= 0:
                result.win = True
                result.final_hp = player.hp
                result.enemy_hp = enemy.hp
                result.damage_taken = starting_hp - player.hp
                result.peak_poison = peak_poison
                return result
        
        # End of turn
        deck_state.discard_hand()
        
        # Enemy turn - POISON TRIGGERS AT START OF ENEMY TURN (BEFORE ACTIONS)
        # Per verified game mechanics: poison triggers at the START of the
        # poisoned creature's turn, then decrements by 1. Poison bypasses block.
        poison_damage = process_poison_tick(enemy)
        
        # Check if enemy died from poison before acting
        if enemy.hp <= 0:
            result.win = True
            result.final_hp = player.hp
            result.enemy_hp = enemy.hp
            result.damage_taken = starting_hp - player.hp
            result.peak_poison = peak_poison
            return result
        
        # Enemy takes action after poison
        if enemy.intent == Intent.ATTACK:
            apply_damage_to_player(player, enemy.intent_value, enemy)
        elif enemy.intent == Intent.BUFF:
            enemy.strength += enemy.intent_value
        elif enemy.intent == Intent.DEFEND:
            enemy.block += enemy.intent_value
        elif enemy.intent == Intent.DEBUFF:
            if player.artifact > 0:
                player.artifact -= 1
            else:
                player.dexterity -= 1
        
        if enemy.hp <= 0:
            result.win = True
            result.final_hp = player.hp
            result.enemy_hp = enemy.hp
            result.damage_taken = starting_hp - player.hp
            result.peak_poison = peak_poison
            return result
        
        decrement_debuffs(enemy)
        
        if player.hp <= 0:
            result.win = False
            result.final_hp = 0
            result.enemy_hp = enemy.hp
            result.damage_taken = starting_hp
            result.peak_poison = peak_poison
            return result
    
    result.win = False
    result.final_hp = player.hp
    result.enemy_hp = enemy.hp
    result.damage_taken = starting_hp - player.hp
    result.peak_poison = peak_poison
    return result


def simulate_run(
    rng: np.random.Generator,
    relic: str = 'none',
    enemy_hp: int = 100,
    max_turns: int = 50
) -> CombatResult:
    """
    Simulate a single Silent run.
    
    Args:
        rng: Random number generator.
        relic: Relic name.
        enemy_hp: Enemy starting HP.
        max_turns: Maximum turns.
    
    Returns:
        CombatResult with outcome.
    """
    player = create_silent_player(relic)
    enemy = EnemyState(name="Act1Elite", hp=enemy_hp, max_hp=enemy_hp)
    deck = create_starter_deck('Silent')
    
    return simulate_combat(player, enemy, deck, rng, max_turns)
