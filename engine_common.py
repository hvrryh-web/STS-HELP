"""
Common engine components for Slay the Spire simulation.
Provides data models, deck/hand utilities, and draw/reshuffle semantics.

Resolution for G2 (Deck/hand fidelity) and G3 (Block/defense modeling).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable, Any
import numpy as np


class CardType(Enum):
    """Card type enumeration."""
    ATTACK = "attack"
    SKILL = "skill"
    POWER = "power"
    STATUS = "status"
    CURSE = "curse"


class Intent(Enum):
    """Enemy intent enumeration."""
    ATTACK = "attack"
    DEFEND = "defend"
    BUFF = "buff"
    DEBUFF = "debuff"
    UNKNOWN = "unknown"


@dataclass
class Card:
    """
    Card data model.
    
    Attributes:
        name: Card name.
        cost: Energy cost.
        card_type: Type of card.
        effects: Dict of effect name to value.
        upgraded: Whether the card is upgraded.
        innate: Whether the card is innate (drawn first turn).
        ethereal: Whether the card is ethereal (exhaust if not played).
        exhaust: Whether the card exhausts on play.
    """
    name: str
    cost: int
    card_type: CardType
    effects: Dict[str, Any] = field(default_factory=dict)
    upgraded: bool = False
    innate: bool = False
    ethereal: bool = False
    exhaust: bool = False
    
    def __hash__(self):
        return hash((self.name, self.upgraded))
    
    def copy(self) -> 'Card':
        """Create a copy of this card."""
        return Card(
            name=self.name,
            cost=self.cost,
            card_type=self.card_type,
            effects=dict(self.effects),
            upgraded=self.upgraded,
            innate=self.innate,
            ethereal=self.ethereal,
            exhaust=self.exhaust
        )


@dataclass
class PlayerState:
    """
    Player state during combat.
    
    Attributes:
        hp: Current health points.
        max_hp: Maximum health points.
        block: Current block.
        energy: Current energy.
        max_energy: Maximum energy per turn.
        strength: Current strength.
        dexterity: Current dexterity.
        artifact: Artifact stacks (blocks debuffs).
        poison: Poison stacks on player (if any).
        orbs: List of orbs (for Defect).
        orb_slots: Maximum orb slots.
        stance: Current stance (for Watcher).
        relics: List of relic names.
    """
    hp: int = 80
    max_hp: int = 80
    block: int = 0
    energy: int = 3
    max_energy: int = 3
    strength: int = 0
    dexterity: int = 0
    artifact: int = 0
    poison: int = 0
    orbs: List[str] = field(default_factory=list)
    orb_slots: int = 3
    stance: str = "neutral"
    relics: List[str] = field(default_factory=list)


@dataclass
class EnemyState:
    """
    Enemy state during combat.
    
    Attributes:
        name: Enemy name.
        hp: Current health points.
        max_hp: Maximum health points.
        block: Current block.
        strength: Current strength.
        poison: Poison stacks.
        vulnerable: Vulnerable stacks.
        weak: Weak stacks.
        artifact: Artifact stacks.
        intent: Current intent.
        intent_value: Value associated with intent (e.g., damage amount).
    """
    name: str = "Enemy"
    hp: int = 100
    max_hp: int = 100
    block: int = 0
    strength: int = 0
    poison: int = 0
    vulnerable: int = 0
    weak: int = 0
    artifact: int = 0
    intent: Intent = Intent.ATTACK
    intent_value: int = 10


@dataclass
class DeckState:
    """
    Deck state during combat.
    
    Resolution for G2: Explicit deck/hand/discard/reshuffle semantics.
    
    Attributes:
        draw_pile: Cards in draw pile.
        hand: Cards in hand.
        discard_pile: Cards in discard pile.
        exhaust_pile: Cards exhausted.
        hand_limit: Maximum hand size.
    """
    draw_pile: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    discard_pile: List[Card] = field(default_factory=list)
    exhaust_pile: List[Card] = field(default_factory=list)
    hand_limit: int = 10
    
    def shuffle_draw_pile(self, rng: np.random.Generator) -> None:
        """Shuffle the draw pile using the provided RNG."""
        rng.shuffle(self.draw_pile)
    
    def draw_cards(self, count: int, rng: np.random.Generator) -> List[Card]:
        """
        Draw cards from the draw pile to hand.
        
        If draw pile is empty, reshuffles discard pile into draw pile.
        Respects hand limit.
        
        Args:
            count: Number of cards to draw.
            rng: Random number generator.
        
        Returns:
            List of cards drawn.
        """
        drawn = []
        for _ in range(count):
            if len(self.hand) >= self.hand_limit:
                break
            
            if not self.draw_pile:
                if not self.discard_pile:
                    break
                # Reshuffle discard into draw pile
                self.draw_pile = self.discard_pile.copy()
                self.discard_pile = []
                self.shuffle_draw_pile(rng)
            
            if self.draw_pile:
                card = self.draw_pile.pop()
                self.hand.append(card)
                drawn.append(card)
        
        return drawn
    
    def discard_card(self, card: Card) -> None:
        """Discard a card from hand."""
        if card in self.hand:
            self.hand.remove(card)
            self.discard_pile.append(card)
    
    def exhaust_card(self, card: Card) -> None:
        """Exhaust a card from hand."""
        if card in self.hand:
            self.hand.remove(card)
            self.exhaust_pile.append(card)
    
    def discard_hand(self) -> None:
        """Discard entire hand to discard pile."""
        self.discard_pile.extend(self.hand)
        self.hand = []
    
    def total_cards(self) -> int:
        """Return total number of cards in deck."""
        return (len(self.draw_pile) + len(self.hand) + 
                len(self.discard_pile) + len(self.exhaust_pile))


@dataclass
class CombatResult:
    """
    Result of a combat simulation.
    
    Attributes:
        win: Whether player won.
        turns: Number of turns taken.
        damage_taken: Total damage taken by player.
        final_hp: Player HP at end of combat.
        enemy_hp: Enemy HP at end of combat.
        peak_poison: Maximum poison applied.
        peak_strength: Maximum strength gained.
        peak_orbs: Maximum orbs channeled (Defect).
        cards_played: Total cards played.
    """
    win: bool = False
    turns: int = 0
    damage_taken: int = 0
    final_hp: int = 0
    enemy_hp: int = 0
    peak_poison: int = 0
    peak_strength: int = 0
    peak_orbs: int = 0
    cards_played: int = 0


def apply_damage_to_enemy(
    enemy: EnemyState,
    damage: int,
    player: PlayerState
) -> int:
    """
    Apply damage to enemy, accounting for block and vulnerability.
    
    Args:
        enemy: Enemy state.
        damage: Base damage amount.
        player: Player state (for strength).
    
    Returns:
        Actual damage dealt.
    """
    # Add strength to damage
    total_damage = damage + player.strength
    
    # Apply vulnerability multiplier (50% more damage)
    if enemy.vulnerable > 0:
        total_damage = int(total_damage * 1.5)
    
    # Apply against block first
    if enemy.block >= total_damage:
        enemy.block -= total_damage
        return 0
    else:
        actual_damage = total_damage - enemy.block
        enemy.block = 0
        enemy.hp -= actual_damage
        return actual_damage


def apply_damage_to_player(
    player: PlayerState,
    damage: int,
    enemy: EnemyState
) -> int:
    """
    Apply damage to player, accounting for block and weakness.
    
    Resolution for G3: Block/defense modeling.
    
    Args:
        player: Player state.
        damage: Base damage amount.
        enemy: Enemy state (for strength).
    
    Returns:
        Actual damage dealt.
    """
    # Add enemy strength
    total_damage = damage + enemy.strength
    
    # Apply weakness (25% less damage)
    if enemy.weak > 0:
        total_damage = int(total_damage * 0.75)
    
    # Apply against block first
    if player.block >= total_damage:
        player.block -= total_damage
        return 0
    else:
        actual_damage = total_damage - player.block
        player.block = 0
        player.hp -= actual_damage
        return actual_damage


def apply_poison(
    target: EnemyState,
    amount: int
) -> bool:
    """
    Apply poison to target, respecting artifact.
    
    Resolution for G4: Artifact semantics.
    Artifact consumes one application event, not magnitude.
    
    Args:
        target: Enemy state.
        amount: Poison amount to apply.
    
    Returns:
        True if poison was applied, False if blocked by artifact.
    """
    if target.artifact > 0:
        target.artifact -= 1
        return False
    target.poison += amount
    return True


def apply_debuff(
    target: EnemyState,
    debuff: str,
    amount: int
) -> bool:
    """
    Apply a debuff to target, respecting artifact.
    
    Args:
        target: Enemy state.
        debuff: Debuff type ('vulnerable', 'weak').
        amount: Debuff stacks to apply.
    
    Returns:
        True if debuff was applied, False if blocked by artifact.
    """
    if target.artifact > 0:
        target.artifact -= 1
        return False
    
    if debuff == 'vulnerable':
        target.vulnerable += amount
    elif debuff == 'weak':
        target.weak += amount
    
    return True


def process_poison_tick(enemy: EnemyState) -> int:
    """
    Process poison damage at end of enemy turn.
    
    Args:
        enemy: Enemy state.
    
    Returns:
        Poison damage dealt.
    """
    if enemy.poison > 0:
        damage = enemy.poison
        enemy.hp -= damage
        enemy.poison -= 1
        return damage
    return 0


def decrement_debuffs(enemy: EnemyState) -> None:
    """Decrement enemy debuff stacks at end of turn."""
    if enemy.vulnerable > 0:
        enemy.vulnerable -= 1
    if enemy.weak > 0:
        enemy.weak -= 1


def create_starter_deck(character: str) -> List[Card]:
    """
    Create a starter deck for the given character.
    
    Args:
        character: Character name.
    
    Returns:
        List of starter cards.
    """
    if character == 'Ironclad':
        return _create_ironclad_starter()
    elif character == 'Silent':
        return _create_silent_starter()
    elif character == 'Defect':
        return _create_defect_starter()
    elif character == 'Watcher':
        return _create_watcher_starter()
    else:
        return _create_ironclad_starter()


def _create_ironclad_starter() -> List[Card]:
    """Create Ironclad starter deck (10 cards)."""
    deck = []
    # 5 Strikes
    for _ in range(5):
        deck.append(Card(
            name="Strike",
            cost=1,
            card_type=CardType.ATTACK,
            effects={'damage': 6}
        ))
    # 4 Defends
    for _ in range(4):
        deck.append(Card(
            name="Defend",
            cost=1,
            card_type=CardType.SKILL,
            effects={'block': 5}
        ))
    # 1 Bash
    deck.append(Card(
        name="Bash",
        cost=2,
        card_type=CardType.ATTACK,
        effects={'damage': 8, 'vulnerable': 2}
    ))
    return deck


def _create_silent_starter() -> List[Card]:
    """Create Silent starter deck (12 cards)."""
    deck = []
    # 5 Strikes
    for _ in range(5):
        deck.append(Card(
            name="Strike",
            cost=1,
            card_type=CardType.ATTACK,
            effects={'damage': 6}
        ))
    # 5 Defends
    for _ in range(5):
        deck.append(Card(
            name="Defend",
            cost=1,
            card_type=CardType.SKILL,
            effects={'block': 5}
        ))
    # 1 Survivor
    deck.append(Card(
        name="Survivor",
        cost=1,
        card_type=CardType.SKILL,
        effects={'block': 8, 'discard': 1}
    ))
    # 1 Neutralize
    deck.append(Card(
        name="Neutralize",
        cost=0,
        card_type=CardType.ATTACK,
        effects={'damage': 3, 'weak': 1}
    ))
    return deck


def _create_defect_starter() -> List[Card]:
    """Create Defect starter deck (12 cards)."""
    deck = []
    # 4 Strikes
    for _ in range(4):
        deck.append(Card(
            name="Strike",
            cost=1,
            card_type=CardType.ATTACK,
            effects={'damage': 6}
        ))
    # 4 Defends
    for _ in range(4):
        deck.append(Card(
            name="Defend",
            cost=1,
            card_type=CardType.SKILL,
            effects={'block': 5}
        ))
    # 1 Zap
    deck.append(Card(
        name="Zap",
        cost=1,
        card_type=CardType.SKILL,
        effects={'channel': 'lightning'}
    ))
    # 1 Dualcast - evokes the rightmost orb twice
    deck.append(Card(
        name="Dualcast",
        cost=1,
        card_type=CardType.SKILL,
        effects={'evoke': 2}  # Evoke count: triggers orb evoke effect this many times
    ))
    return deck


def _create_watcher_starter() -> List[Card]:
    """Create Watcher starter deck (10 cards)."""
    deck = []
    # 4 Strikes
    for _ in range(4):
        deck.append(Card(
            name="Strike",
            cost=1,
            card_type=CardType.ATTACK,
            effects={'damage': 6}
        ))
    # 4 Defends
    for _ in range(4):
        deck.append(Card(
            name="Defend",
            cost=1,
            card_type=CardType.SKILL,
            effects={'block': 5}
        ))
    # 1 Eruption
    deck.append(Card(
        name="Eruption",
        cost=2,
        card_type=CardType.ATTACK,
        effects={'damage': 9, 'enter_stance': 'wrath'}
    ))
    # 1 Vigilance
    deck.append(Card(
        name="Vigilance",
        cost=2,
        card_type=CardType.SKILL,
        effects={'block': 8, 'enter_stance': 'calm'}
    ))
    return deck


def get_playable_cards(
    deck_state: DeckState,
    player: PlayerState
) -> List[Card]:
    """
    Get list of playable cards from hand.
    
    Args:
        deck_state: Current deck state.
        player: Current player state.
    
    Returns:
        List of cards that can be played with current energy.
    """
    return [card for card in deck_state.hand if card.cost <= player.energy]
