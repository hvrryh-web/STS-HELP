"""
Defect engine for Slay the Spire simulation.
Implements orb mechanics (Lightning, Frost, Dark, Plasma) and focus scaling.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np

from engine_common import (
    Card, CardType, PlayerState, EnemyState, DeckState, CombatResult,
    Intent, apply_damage_to_enemy, apply_damage_to_player,
    decrement_debuffs, create_starter_deck, get_playable_cards
)


# Defect-specific cards
DEFECT_CARDS = {
    'Ball Lightning': Card(
        name='Ball Lightning',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 7, 'channel': 'lightning'}
    ),
    'Cold Snap': Card(
        name='Cold Snap',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 6, 'channel': 'frost'}
    ),
    'Compile Driver': Card(
        name='Compile Driver',
        cost=1,
        card_type=CardType.ATTACK,
        effects={'damage': 7, 'draw_per_orb_type': True}
    ),
    'Defragment': Card(
        name='Defragment',
        cost=1,
        card_type=CardType.POWER,
        effects={'focus': 1}
    ),
    'Electrodynamics': Card(
        name='Electrodynamics',
        cost=2,
        card_type=CardType.POWER,
        effects={'lightning_aoe': True}
    ),
    'Glacier': Card(
        name='Glacier',
        cost=2,
        card_type=CardType.SKILL,
        effects={'block': 7, 'channel_frost': 2}
    ),
    'Capacitor': Card(
        name='Capacitor',
        cost=1,
        card_type=CardType.POWER,
        effects={'orb_slots': 2}
    ),
    'Loop': Card(
        name='Loop',
        cost=1,
        card_type=CardType.POWER,
        effects={'passive_trigger': True}
    ),
    'Consume': Card(
        name='Consume',
        cost=2,
        card_type=CardType.SKILL,
        effects={'focus': 2, 'remove_orb_slot': True}
    ),
    'Claw': Card(
        name='Claw',
        cost=0,
        card_type=CardType.ATTACK,
        effects={'damage': 3, 'claw_bonus': True}
    ),
}


@dataclass
class Orb:
    """Orb data model."""
    orb_type: str  # 'lightning', 'frost', 'dark', 'plasma'
    
    def get_passive_value(self, focus: int) -> int:
        """Get passive trigger value."""
        base = {
            'lightning': 3,
            'frost': 2,
            'dark': 6,
            'plasma': 1
        }.get(self.orb_type, 0)
        return max(0, base + focus)
    
    def get_evoke_value(self, focus: int) -> int:
        """Get evoke trigger value."""
        base = {
            'lightning': 8,
            'frost': 5,
            'dark': 0,  # Dark evoke = accumulated passive
            'plasma': 2  # Gain 2 energy
        }.get(self.orb_type, 0)
        return max(0, base + focus)


@dataclass
class DefectState(PlayerState):
    """Extended player state for Defect with orb and focus tracking."""
    focus: int = 0
    orb_list: List[Orb] = field(default_factory=list)
    lightning_aoe: bool = False
    loop_passive: bool = False
    claw_damage_bonus: int = 0
    dark_accumulated: int = 0


def create_defect_player(relic: str = 'none') -> DefectState:
    """
    Create Defect player state with starting stats.
    
    Args:
        relic: Starting relic name.
    
    Returns:
        DefectState configured for Defect.
    """
    player = DefectState(
        hp=75,
        max_hp=75,
        energy=3,
        max_energy=3,
        orb_slots=3,
        relics=[relic] if relic != 'none' else []
    )
    
    # Cracked Core: channel 1 Lightning at start of combat
    if relic == 'none' or relic == 'cracked_core':
        player.orb_list.append(Orb('lightning'))
    
    return player


def channel_orb(player: DefectState, orb_type: str) -> None:
    """
    Channel an orb.
    
    Args:
        player: Player state.
        orb_type: Type of orb to channel.
    """
    new_orb = Orb(orb_type)
    
    if len(player.orb_list) >= player.orb_slots:
        # Evoke oldest orb
        evoke_orb(player, 0)
    
    player.orb_list.append(new_orb)


def evoke_orb(player: DefectState, index: int = 0, enemy: Optional[EnemyState] = None) -> int:
    """
    Evoke an orb at the specified index.
    
    Args:
        player: Player state.
        index: Index of orb to evoke.
        enemy: Enemy state (for damage).
    
    Returns:
        Damage dealt (if any).
    """
    if index >= len(player.orb_list):
        return 0
    
    orb = player.orb_list.pop(index)
    evoke_value = orb.get_evoke_value(player.focus)
    
    if orb.orb_type == 'lightning':
        if enemy:
            enemy.hp -= evoke_value
        return evoke_value
    elif orb.orb_type == 'frost':
        player.block += evoke_value
        return 0
    elif orb.orb_type == 'dark':
        if enemy:
            damage = player.dark_accumulated
            enemy.hp -= damage
            player.dark_accumulated = 0
            return damage
        return 0
    elif orb.orb_type == 'plasma':
        player.energy += evoke_value
        return 0
    
    return 0


def process_orb_passives(player: DefectState, enemy: EnemyState) -> int:
    """
    Process passive orb effects at end of turn.
    
    Args:
        player: Player state.
        enemy: Enemy state.
    
    Returns:
        Total damage dealt.
    """
    total_damage = 0
    trigger_count = 2 if player.loop_passive else 1
    
    for _ in range(trigger_count):
        for orb in player.orb_list:
            passive_value = orb.get_passive_value(player.focus)
            
            if orb.orb_type == 'lightning':
                # Deal damage to random enemy
                if player.lightning_aoe:
                    # AoE not relevant for single enemy
                    pass
                enemy.hp -= passive_value
                total_damage += passive_value
            elif orb.orb_type == 'frost':
                player.block += passive_value
            elif orb.orb_type == 'dark':
                player.dark_accumulated += passive_value
    
    return total_damage


def get_enemy_intent(enemy: EnemyState, rng: np.random.Generator, turn: int) -> Tuple[Intent, int]:
    """
    Generate enemy intent.
    
    Based on Act 1 Elite patterns, damage is calibrated to create 
    realistic win rates of 40-70% for starter decks.
    """
    roll = rng.random()
    
    if turn == 1:
        # Strong opening attack
        return Intent.ATTACK, enemy.strength + 17
    elif roll < 0.65:
        # After turn 1: 65% chance to attack with scaling damage
        attack_damage = 13 + enemy.strength + (turn // 2) * 3
        return Intent.ATTACK, attack_damage
    elif roll < 0.85:
        # After turn 1: 20% chance to buff
        return Intent.BUFF, 3
    else:
        # After turn 1: 15% chance to defend
        return Intent.DEFEND, 14


def evaluate_card_value(
    card: Card,
    player: DefectState,
    enemy: EnemyState,
    deck_state: DeckState
) -> float:
    """Evaluate the value of playing a card."""
    value = 0.0
    effects = card.effects
    
    # Damage
    if 'damage' in effects:
        base_damage = effects['damage'] + player.strength
        if effects.get('claw_bonus'):
            base_damage += player.claw_damage_bonus
        if enemy.vulnerable > 0:
            base_damage = int(base_damage * 1.5)
        value += min(base_damage, enemy.hp) * 0.8
    
    # Block
    if 'block' in effects:
        block_amount = effects['block'] + player.dexterity
        if enemy.intent == Intent.ATTACK:
            value += min(block_amount, enemy.intent_value) * 1.2
        else:
            value += block_amount * 0.3
    
    # Channel orbs
    if 'channel' in effects:
        orb_type = effects['channel']
        if orb_type == 'lightning':
            # Estimate passive + evoke value
            value += (3 + player.focus) * 3 + 8  # Passive * turns + evoke
        elif orb_type == 'frost':
            value += (2 + player.focus) * 2
    
    if 'channel_frost' in effects:
        value += (2 + player.focus) * effects['channel_frost'] * 2
    
    # Focus
    if 'focus' in effects:
        orb_count = len(player.orb_list)
        turns_estimate = max(1, enemy.hp // 20)
        value += effects['focus'] * orb_count * turns_estimate
    
    # Orb slots
    if 'orb_slots' in effects:
        value += effects['orb_slots'] * 10
    
    # Claw bonus
    if effects.get('claw_bonus'):
        value += player.claw_damage_bonus * 0.5
    
    if card.cost > 0:
        value /= card.cost
    
    return value


def select_card_to_play(
    deck_state: DeckState,
    player: DefectState,
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
    player: DefectState,
    enemy: EnemyState,
    deck_state: DeckState,
    rng: np.random.Generator
) -> None:
    """Execute the effects of playing a card."""
    player.energy -= card.cost
    effects = card.effects
    
    # Damage
    if 'damage' in effects:
        base_damage = effects['damage'] + player.strength
        if effects.get('claw_bonus'):
            base_damage += player.claw_damage_bonus
            player.claw_damage_bonus += 2  # Claw increases damage
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
    
    # Channel orb
    if 'channel' in effects:
        channel_orb(player, effects['channel'])
    
    if 'channel_frost' in effects:
        for _ in range(effects['channel_frost']):
            channel_orb(player, 'frost')
    
    # Focus
    if 'focus' in effects:
        player.focus += effects['focus']
    
    # Orb slots
    if 'orb_slots' in effects:
        player.orb_slots += effects['orb_slots']
    
    if effects.get('remove_orb_slot'):
        player.orb_slots = max(0, player.orb_slots - 1)
        if len(player.orb_list) > player.orb_slots:
            player.orb_list = player.orb_list[:player.orb_slots]
    
    # Lightning AOE
    if effects.get('lightning_aoe'):
        player.lightning_aoe = True
    
    # Loop passive
    if effects.get('passive_trigger'):
        player.loop_passive = True
    
    # Evoke
    if 'evoke' in effects:
        for _ in range(effects['evoke']):
            if player.orb_list:
                evoke_orb(player, 0, enemy)
    
    # Draw per orb type
    if effects.get('draw_per_orb_type'):
        orb_types = set(o.orb_type for o in player.orb_list)
        deck_state.draw_cards(len(orb_types), rng)
    
    # Handle card destination
    if card.exhaust:
        deck_state.exhaust_card(card)
    else:
        deck_state.discard_card(card)


def simulate_combat(
    player: DefectState,
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
    peak_orbs = len(player.orb_list)
    
    for turn in range(1, max_turns + 1):
        result.turns = turn
        
        # Start of turn
        player.block = 0
        player.energy = player.max_energy
        
        deck_state.draw_cards(5, rng)
        
        enemy.intent, enemy.intent_value = get_enemy_intent(enemy, rng, turn)
        
        # Play cards
        while player.energy > 0 or any(c.cost == 0 for c in deck_state.hand):
            card = select_card_to_play(deck_state, player, enemy)
            if card is None:
                break
            play_card(card, player, enemy, deck_state, rng)
            result.cards_played += 1
            
            if len(player.orb_list) > peak_orbs:
                peak_orbs = len(player.orb_list)
            
            if enemy.hp <= 0:
                result.win = True
                result.final_hp = player.hp
                result.enemy_hp = enemy.hp
                result.damage_taken = starting_hp - player.hp
                result.peak_orbs = peak_orbs
                return result
        
        # End of turn: process orb passives
        passive_damage = process_orb_passives(player, enemy)
        
        if enemy.hp <= 0:
            result.win = True
            result.final_hp = player.hp
            result.enemy_hp = enemy.hp
            result.damage_taken = starting_hp - player.hp
            result.peak_orbs = peak_orbs
            return result
        
        deck_state.discard_hand()
        
        # Enemy turn
        if enemy.intent == Intent.ATTACK:
            apply_damage_to_player(player, enemy.intent_value, enemy)
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
            result.peak_orbs = peak_orbs
            return result
    
    result.win = False
    result.final_hp = player.hp
    result.enemy_hp = enemy.hp
    result.damage_taken = starting_hp - player.hp
    result.peak_orbs = peak_orbs
    return result


def simulate_run(
    rng: np.random.Generator,
    relic: str = 'none',
    enemy_hp: int = 110,
    max_turns: int = 50
) -> CombatResult:
    """Simulate a single Defect run."""
    player = create_defect_player(relic)
    enemy = EnemyState(name="Act1Elite", hp=enemy_hp, max_hp=enemy_hp)
    deck = create_starter_deck('Defect')
    
    return simulate_combat(player, enemy, deck, rng, max_turns)
