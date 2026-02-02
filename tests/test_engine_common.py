"""
Unit tests for engine common components.
Resolution for R2, R3, R4: Verification of deck/hand fidelity, block, and artifact semantics.
"""

import pytest
import numpy as np

from engine_common import (
    Card, CardType, PlayerState, EnemyState, DeckState,
    apply_damage_to_enemy, apply_damage_to_player,
    apply_poison, apply_debuff, process_poison_tick,
    create_starter_deck
)


class TestDeckState:
    """Tests for DeckState and draw/reshuffle semantics."""
    
    def test_deck_initialization(self):
        """Deck state initializes correctly."""
        cards = [Card("Strike", 1, CardType.ATTACK) for _ in range(5)]
        deck = DeckState(draw_pile=cards)
        
        assert len(deck.draw_pile) == 5
        assert len(deck.hand) == 0
        assert len(deck.discard_pile) == 0
    
    def test_draw_cards_basic(self):
        """Drawing cards moves them from draw pile to hand."""
        rng = np.random.default_rng(42)
        cards = [Card(f"Card{i}", 1, CardType.ATTACK) for i in range(10)]
        deck = DeckState(draw_pile=cards.copy())
        
        drawn = deck.draw_cards(5, rng)
        
        assert len(drawn) == 5
        assert len(deck.hand) == 5
        assert len(deck.draw_pile) == 5
    
    def test_draw_cards_reshuffle(self):
        """Drawing from empty deck reshuffles discard pile."""
        rng = np.random.default_rng(42)
        cards = [Card(f"Card{i}", 1, CardType.ATTACK) for i in range(5)]
        deck = DeckState(draw_pile=[], discard_pile=cards.copy())
        
        initial_discard = len(deck.discard_pile)
        drawn = deck.draw_cards(3, rng)
        
        assert len(drawn) == 3
        assert len(deck.hand) == 3
        assert len(deck.discard_pile) == 0
        assert len(deck.draw_pile) == 2
    
    def test_draw_cards_hand_limit(self):
        """Drawing respects hand limit."""
        rng = np.random.default_rng(42)
        cards = [Card(f"Card{i}", 1, CardType.ATTACK) for i in range(15)]
        deck = DeckState(draw_pile=cards.copy(), hand_limit=10)
        
        drawn = deck.draw_cards(12, rng)
        
        assert len(drawn) == 10  # Limited by hand size
        assert len(deck.hand) == 10
    
    def test_discard_card(self):
        """Discarding moves card from hand to discard pile."""
        card = Card("Strike", 1, CardType.ATTACK)
        deck = DeckState(hand=[card])
        
        deck.discard_card(card)
        
        assert len(deck.hand) == 0
        assert len(deck.discard_pile) == 1
    
    def test_exhaust_card(self):
        """Exhausting moves card from hand to exhaust pile."""
        card = Card("Limit Break", 1, CardType.SKILL, exhaust=True)
        deck = DeckState(hand=[card])
        
        deck.exhaust_card(card)
        
        assert len(deck.hand) == 0
        assert len(deck.exhaust_pile) == 1
    
    def test_total_cards_conservation(self):
        """Total cards remains constant through operations."""
        rng = np.random.default_rng(42)
        cards = [Card(f"Card{i}", 1, CardType.ATTACK) for i in range(10)]
        deck = DeckState(draw_pile=cards.copy())
        
        initial_total = deck.total_cards()
        
        deck.draw_cards(5, rng)
        assert deck.total_cards() == initial_total
        
        deck.discard_hand()
        assert deck.total_cards() == initial_total


class TestBlockMechanics:
    """Tests for block/defense modeling (Resolution R3)."""
    
    def test_block_reduces_damage(self):
        """Block reduces incoming damage."""
        player = PlayerState(hp=80, block=10)
        enemy = EnemyState()
        
        damage = apply_damage_to_player(player, 15, enemy)
        
        assert damage == 5  # 15 - 10 block
        assert player.hp == 75
        assert player.block == 0
    
    def test_block_fully_absorbs(self):
        """Block can fully absorb damage."""
        player = PlayerState(hp=80, block=20)
        enemy = EnemyState()
        
        damage = apply_damage_to_player(player, 15, enemy)
        
        assert damage == 0
        assert player.hp == 80
        assert player.block == 5
    
    def test_enemy_weakness_reduces_damage(self):
        """Enemy weakness reduces outgoing damage."""
        player = PlayerState(hp=80)
        enemy = EnemyState(weak=1)
        
        damage = apply_damage_to_player(player, 20, enemy)
        
        assert damage == 15  # 20 * 0.75 = 15
    
    def test_vulnerability_increases_damage(self):
        """Vulnerability increases damage taken."""
        player = PlayerState(strength=0)
        enemy = EnemyState(hp=100, vulnerable=1)
        
        apply_damage_to_enemy(enemy, 10, player)
        
        assert enemy.hp == 85  # 100 - 10 * 1.5


class TestArtifactSemantics:
    """Tests for artifact semantics (Resolution R4)."""
    
    def test_artifact_blocks_poison_application(self):
        """Artifact blocks poison application event."""
        enemy = EnemyState(artifact=1)
        
        result = apply_poison(enemy, 5)
        
        assert result is False
        assert enemy.poison == 0
        assert enemy.artifact == 0
    
    def test_artifact_blocks_single_event(self):
        """Artifact consumes one application, not magnitude."""
        enemy = EnemyState(artifact=1)
        
        # First application blocked
        apply_poison(enemy, 10)
        assert enemy.poison == 0
        assert enemy.artifact == 0
        
        # Second application succeeds
        apply_poison(enemy, 5)
        assert enemy.poison == 5
    
    def test_artifact_blocks_debuff(self):
        """Artifact blocks debuff application."""
        enemy = EnemyState(artifact=1)
        
        result = apply_debuff(enemy, 'vulnerable', 2)
        
        assert result is False
        assert enemy.vulnerable == 0
        assert enemy.artifact == 0
    
    def test_poison_without_artifact(self):
        """Poison applies normally without artifact."""
        enemy = EnemyState()
        
        result = apply_poison(enemy, 5)
        
        assert result is True
        assert enemy.poison == 5


class TestPoisonMechanics:
    """Tests for poison mechanics."""
    
    def test_poison_tick_damages(self):
        """Poison deals damage at end of turn."""
        enemy = EnemyState(hp=100, poison=5)
        
        damage = process_poison_tick(enemy)
        
        assert damage == 5
        assert enemy.hp == 95
        assert enemy.poison == 4
    
    def test_poison_decrements(self):
        """Poison decrements each tick."""
        enemy = EnemyState(hp=100, poison=3)
        
        for expected in [3, 2, 1]:
            damage = process_poison_tick(enemy)
            assert damage == expected
        
        assert enemy.poison == 0


class TestStarterDecks:
    """Tests for starter deck creation."""
    
    def test_ironclad_starter(self):
        """Ironclad starter deck has correct composition."""
        deck = create_starter_deck('Ironclad')
        
        assert len(deck) == 10
        strikes = [c for c in deck if c.name == 'Strike']
        defends = [c for c in deck if c.name == 'Defend']
        bashes = [c for c in deck if c.name == 'Bash']
        
        assert len(strikes) == 5
        assert len(defends) == 4
        assert len(bashes) == 1
    
    def test_silent_starter(self):
        """Silent starter deck has correct composition."""
        deck = create_starter_deck('Silent')
        
        assert len(deck) == 12
        strikes = [c for c in deck if c.name == 'Strike']
        defends = [c for c in deck if c.name == 'Defend']
        
        assert len(strikes) == 5
        assert len(defends) == 5
    
    def test_defect_starter(self):
        """Defect starter deck has correct composition."""
        deck = create_starter_deck('Defect')
        
        assert len(deck) == 10
        zaps = [c for c in deck if c.name == 'Zap']
        
        assert len(zaps) == 1
    
    def test_watcher_starter(self):
        """Watcher starter deck has correct composition."""
        deck = create_starter_deck('Watcher')
        
        assert len(deck) == 10
        eruptions = [c for c in deck if c.name == 'Eruption']
        vigilances = [c for c in deck if c.name == 'Vigilance']
        
        assert len(eruptions) == 1
        assert len(vigilances) == 1
