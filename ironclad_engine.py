"""
Ironclad engine for Slay the Spire simulation.
Implements explicit deck/hand/energy simulation with strength scaling.

Ironclad is used as the calibration anchor for the simulation system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

from engine_common import (
    Card, CardType, PlayerState, EnemyState, DeckState, CombatResult,
    Intent, apply_damage_to_enemy, apply_damage_to_player,
    apply_debuff, decrement_debuffs, create_starter_deck,
    get_playable_cards
)


# Ironclad-specific cards
IRONCLAD_CARDS = {
    'Inflame': Card(
        name='Inflame',
        cost=1,
        card_type=CardType.POWER,
        effects={'strength': 2}
    ),
    'Shrug It Off': Card(
        name='Shrug It Off',
        cost=1,
        card_type=CardType.SKILL,
        effects={'block': 8, 'draw': 1}
    ),
    'Heavy Blade': Card(
        name='Heavy Blade',
        cost=2,
        card_type=CardType.ATTACK,
        effects={'damage': 14, 'strength_multiplier': 3}
    ),
    'Limit Break': Card(
        name='Limit Break',
        cost=1,
        card_type=CardType.SKILL,
        effects={'double_strength': True},
        exhaust=True
    ),
    'Clothesline': Card(
        name='Clothesline',
        cost=2,
        card_type=CardType.ATTACK,
        effects={'damage': 12, 'weak': 2}
    ),
    'Iron Wave': Card(
        name='Iron Wave',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 5, 'block': 5}
    ),
    'Pommel Strike': Card(
        name='Pommel Strike',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 9, 'draw': 1}
    ),
    'Headbutt': Card(
        name='Headbutt',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 9, 'put_on_top': True}
    ),
    'Anger': Card(
        name='Anger',
        cost=0,
        card_type=CardType.ATTACK,
        effects={'damage': 6, 'add_to_discard': True}
    ),
    'Carnage': Card(
        name='Carnage',
        cost=2,
        card_type=CardType.ATTACK,
        effects={'damage': 20},
        ethereal=True
    ),
}


def create_ironclad_player(relic: str = 'none') -> PlayerState:
    """
    Create Ironclad player state with starting stats.
    
    Args:
        relic: Starting relic name.
    
    Returns:
        PlayerState configured for Ironclad.
    """
    player = PlayerState(
        hp=80,
        max_hp=80,
        energy=3,
        max_energy=3,
        relics=[relic] if relic != 'none' else []
    )
    
    # Apply relic effects
    if relic == 'burning_blood':
        pass  # Heals 6 HP at end of combat (passive)
    elif relic == 'snecko_eye':
        player.max_energy = 2  # Confused but +2 energy
        player.energy = 2
    
    return player


def get_enemy_intent(enemy: EnemyState, rng: np.random.Generator, turn: int) -> Tuple[Intent, int]:
    """
    Generate enemy intent for the current turn.
    
    Resolution for G3: Intent-aware defensive play.
    
    Args:
        enemy: Enemy state.
        rng: Random number generator.
        turn: Current turn number.
    
    Returns:
        Tuple of (Intent, value).
    """
    # Simplified enemy AI: attack pattern with occasional defense
    roll = rng.random()
    
    if turn == 1:
        # First turn often an attack
        return Intent.ATTACK, enemy.strength + 12
    elif roll < 0.6:
        # 60% chance to attack
        attack_damage = 8 + enemy.strength + (turn // 3) * 2
        return Intent.ATTACK, attack_damage
    elif roll < 0.8:
        # 20% chance to buff
        return Intent.BUFF, 2
    else:
        # 20% chance to defend
        return Intent.DEFEND, 10
    

def evaluate_card_value(
    card: Card,
    player: PlayerState,
    enemy: EnemyState,
    deck_state: DeckState
) -> float:
    """
    Evaluate the value of playing a card.
    
    Resolution for G8: Limited lookahead heuristics.
    
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
        if 'strength_multiplier' in effects:
            base_damage += player.strength * (effects['strength_multiplier'] - 1)
        if enemy.vulnerable > 0:
            base_damage = int(base_damage * 1.5)
        # Value damage relative to enemy HP
        value += min(base_damage, enemy.hp) * 1.0
    
    # Block value (based on expected incoming damage)
    if 'block' in effects:
        block_amount = effects['block'] + player.dexterity
        # Value block based on enemy intent
        if enemy.intent == Intent.ATTACK:
            value += min(block_amount, enemy.intent_value) * 1.2
        else:
            value += block_amount * 0.3
    
    # Strength value (long-term scaling)
    if 'strength' in effects:
        # Estimate remaining turns and cards
        remaining_attacks = sum(
            1 for c in deck_state.draw_pile + deck_state.hand 
            if c.card_type == CardType.ATTACK
        )
        value += effects['strength'] * remaining_attacks * 0.5
    
    # Double strength (Limit Break)
    if effects.get('double_strength'):
        value += player.strength * 2 * 3  # High value if strength is high
    
    # Vulnerable application
    if 'vulnerable' in effects:
        value += effects['vulnerable'] * 5
    
    # Weak application
    if 'weak' in effects:
        value += effects['weak'] * 3
    
    # Draw value
    if 'draw' in effects:
        value += effects['draw'] * 4
    
    # Energy efficiency
    if card.cost > 0:
        value /= card.cost
    
    return value


def select_card_to_play(
    deck_state: DeckState,
    player: PlayerState,
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
    
    # Evaluate each card and select best
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
    player: PlayerState,
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
        base_damage = effects['damage']
        if 'strength_multiplier' in effects:
            base_damage += player.strength * effects['strength_multiplier']
        else:
            base_damage += player.strength
        
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
    
    # Strength
    if 'strength' in effects:
        player.strength += effects['strength']
    
    # Double strength
    if effects.get('double_strength'):
        player.strength *= 2
    
    # Vulnerable
    if 'vulnerable' in effects:
        apply_debuff(enemy, 'vulnerable', effects['vulnerable'])
    
    # Weak
    if 'weak' in effects:
        apply_debuff(enemy, 'weak', effects['weak'])
    
    # Draw
    if 'draw' in effects:
        deck_state.draw_cards(effects['draw'], rng)
    
    # Handle card destination
    if card.exhaust:
        deck_state.exhaust_card(card)
    else:
        deck_state.discard_card(card)


def simulate_combat(
    player: PlayerState,
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
    # Initialize deck state
    deck_state = DeckState(draw_pile=[c.copy() for c in deck])
    deck_state.shuffle_draw_pile(rng)
    
    result = CombatResult()
    starting_hp = player.hp
    peak_strength = 0
    
    for turn in range(1, max_turns + 1):
        result.turns = turn
        
        # Start of turn
        player.block = 0
        player.energy = player.max_energy
        
        # Draw cards (5 by default)
        deck_state.draw_cards(5, rng)
        
        # Get enemy intent for this turn
        enemy.intent, enemy.intent_value = get_enemy_intent(enemy, rng, turn)
        
        # Play cards until no playable cards or no value
        cards_played_this_turn = 0
        while player.energy > 0:
            card = select_card_to_play(deck_state, player, enemy)
            if card is None:
                break
            play_card(card, player, enemy, deck_state, rng)
            cards_played_this_turn += 1
            result.cards_played += 1
            
            # Track peak strength
            if player.strength > peak_strength:
                peak_strength = player.strength
            
            # Check if enemy is dead
            if enemy.hp <= 0:
                result.win = True
                result.final_hp = player.hp
                result.enemy_hp = enemy.hp
                result.damage_taken = starting_hp - player.hp
                result.peak_strength = peak_strength
                return result
        
        # End of turn: discard hand
        deck_state.discard_hand()
        
        # Enemy turn: apply intent
        if enemy.intent == Intent.ATTACK:
            damage_dealt = apply_damage_to_player(player, enemy.intent_value, enemy)
        elif enemy.intent == Intent.BUFF:
            enemy.strength += enemy.intent_value
        elif enemy.intent == Intent.DEFEND:
            enemy.block += enemy.intent_value
        
        # Decrement debuffs
        decrement_debuffs(enemy)
        
        # Check if player is dead
        if player.hp <= 0:
            result.win = False
            result.final_hp = 0
            result.enemy_hp = enemy.hp
            result.damage_taken = starting_hp
            result.peak_strength = peak_strength
            return result
    
    # Timeout: loss
    result.win = False
    result.final_hp = player.hp
    result.enemy_hp = enemy.hp
    result.damage_taken = starting_hp - player.hp
    result.peak_strength = peak_strength
    return result


def simulate_run(
    rng: np.random.Generator,
    relic: str = 'none',
    enemy_hp: int = 120,
    max_turns: int = 50
) -> CombatResult:
    """
    Simulate a single Ironclad run.
    
    Args:
        rng: Random number generator.
        relic: Relic name.
        enemy_hp: Enemy starting HP.
        max_turns: Maximum turns.
    
    Returns:
        CombatResult with outcome.
    """
    player = create_ironclad_player(relic)
    enemy = EnemyState(name="Act1Elite", hp=enemy_hp, max_hp=enemy_hp)
    deck = create_starter_deck('Ironclad')
    
    return simulate_combat(player, enemy, deck, rng, max_turns)
