"""
Unit tests for src.models module.
"""

import pytest
from src.models.card import Card, CardType, Rarity
from src.models.relic import Relic, RelicRarity
from src.models.deck import DeckEvaluation


class TestCard:
    """Tests for Card dataclass."""
    
    def test_card_creation(self):
        """Card can be created with required fields."""
        card = Card(
            name="Strike",
            card_type=CardType.ATTACK,
            cost=1,
            rarity=Rarity.BASIC
        )
        
        assert card.name == "Strike"
        assert card.card_type == CardType.ATTACK
        assert card.cost == 1
        assert card.rarity == Rarity.BASIC
        assert card.tier_grade == "C"
        assert card.tier_score == 50.0
    
    def test_card_with_tier_info(self):
        """Card can be created with tier information."""
        card = Card(
            name="Heavy Blade",
            card_type=CardType.ATTACK,
            cost=2,
            rarity=Rarity.COMMON,
            tier_grade="S",
            tier_score=95.0
        )
        
        assert card.tier_grade == "S"
        assert card.tier_score == 95.0
    
    def test_card_invalid_cost(self):
        """Card rejects invalid cost values."""
        with pytest.raises(ValueError):
            Card(
                name="Invalid",
                card_type=CardType.ATTACK,
                cost=-2,  # Invalid (only -1 is valid for X-cost)
                rarity=Rarity.COMMON
            )
    
    def test_card_invalid_tier_score(self):
        """Card rejects tier scores out of range."""
        with pytest.raises(ValueError):
            Card(
                name="Invalid",
                card_type=CardType.ATTACK,
                cost=1,
                rarity=Rarity.COMMON,
                tier_score=150.0  # Out of range
            )
    
    def test_card_invalid_tier_grade(self):
        """Card rejects invalid tier grades."""
        with pytest.raises(ValueError):
            Card(
                name="Invalid",
                card_type=CardType.ATTACK,
                cost=1,
                rarity=Rarity.COMMON,
                tier_grade="Z"  # Invalid grade
            )
    
    def test_card_get_value(self):
        """Card.get_value returns tier score."""
        card = Card(
            name="Test",
            card_type=CardType.ATTACK,
            cost=1,
            rarity=Rarity.COMMON,
            tier_score=85.0
        )
        
        assert card.get_value() == 85.0
    
    def test_card_has_synergy(self):
        """Card.has_synergy checks synergies and fusion tags."""
        card = Card(
            name="Heavy Blade",
            card_type=CardType.ATTACK,
            cost=2,
            rarity=Rarity.COMMON,
            synergies=["Strength"],
            fusion_tags=["Strength-scaling"]
        )
        
        assert card.has_synergy("Strength")
        assert card.has_synergy("Strength-scaling")
        assert not card.has_synergy("Poison")
    
    def test_card_to_dict(self):
        """Card can be converted to dictionary."""
        card = Card(
            name="Strike",
            card_type=CardType.ATTACK,
            cost=1,
            rarity=Rarity.BASIC
        )
        
        card_dict = card.to_dict()
        
        assert card_dict["name"] == "Strike"
        assert card_dict["card_type"] == "Attack"
        assert card_dict["cost"] == 1
        assert card_dict["rarity"] == "Basic"
    
    def test_card_from_dict(self):
        """Card can be created from dictionary."""
        data = {
            "name": "Defend",
            "card_type": "Skill",
            "cost": 1,
            "rarity": "Basic",
            "tier_grade": "B",
            "tier_score": 65.0
        }
        
        card = Card.from_dict(data)
        
        assert card.name == "Defend"
        assert card.card_type == CardType.SKILL
        assert card.cost == 1
        assert card.tier_score == 65.0


class TestRelic:
    """Tests for Relic dataclass."""
    
    def test_relic_creation(self):
        """Relic can be created with required fields."""
        relic = Relic(
            name="Burning Blood",
            rarity=RelicRarity.STARTER,
            effect="At the end of combat, heal 6 HP."
        )
        
        assert relic.name == "Burning Blood"
        assert relic.rarity == RelicRarity.STARTER
        assert relic.effect == "At the end of combat, heal 6 HP."
        assert relic.tier_score == 50.0
    
    def test_relic_with_synergies(self):
        """Relic can be created with synergies."""
        relic = Relic(
            name="Dead Branch",
            rarity=RelicRarity.RARE,
            effect="Whenever you Exhaust a card, add a random card to your hand.",
            synergies=["Corruption", "Exhaust"],
            tier_score=98.0
        )
        
        assert "Corruption" in relic.synergies
        assert relic.tier_score == 98.0
    
    def test_relic_invalid_tier_score(self):
        """Relic rejects tier scores out of range."""
        with pytest.raises(ValueError):
            Relic(
                name="Invalid",
                rarity=RelicRarity.COMMON,
                effect="Test",
                tier_score=200.0  # Out of range
            )
    
    def test_relic_get_value(self):
        """Relic.get_value returns tier score."""
        relic = Relic(
            name="Test",
            rarity=RelicRarity.RARE,
            effect="Test effect",
            tier_score=85.0
        )
        
        assert relic.get_value() == 85.0
    
    def test_relic_has_synergy(self):
        """Relic.has_synergy checks synergies."""
        relic = Relic(
            name="Vajra",
            rarity=RelicRarity.BOSS,
            effect="Gain 1 Strength at the start of each combat.",
            synergies=["Strength", "Heavy Blade"]
        )
        
        assert relic.has_synergy("Strength")
        assert not relic.has_synergy("Poison")
    
    def test_relic_to_dict(self):
        """Relic can be converted to dictionary."""
        relic = Relic(
            name="Test Relic",
            rarity=RelicRarity.COMMON,
            effect="Test effect"
        )
        
        relic_dict = relic.to_dict()
        
        assert relic_dict["name"] == "Test Relic"
        assert relic_dict["rarity"] == "Common"
        assert relic_dict["effect"] == "Test effect"
    
    def test_relic_from_dict(self):
        """Relic can be created from dictionary."""
        data = {
            "name": "Anchor",
            "rarity": "Uncommon",
            "effect": "Gain 10 Block at the start of each combat.",
            "tier_score": 75.0
        }
        
        relic = Relic.from_dict(data)
        
        assert relic.name == "Anchor"
        assert relic.rarity == RelicRarity.UNCOMMON
        assert relic.tier_score == 75.0


class TestDeckEvaluation:
    """Tests for DeckEvaluation."""
    
    def test_deck_creation(self):
        """DeckEvaluation can be created."""
        cards = [
            Card("Strike", CardType.ATTACK, 1, Rarity.BASIC, tier_score=50),
            Card("Defend", CardType.SKILL, 1, Rarity.BASIC, tier_score=55),
        ]
        
        deck = DeckEvaluation(cards=cards, name="Test Deck")
        
        assert deck.name == "Test Deck"
        assert len(deck.cards) == 2
    
    def test_calculate_card_quality(self):
        """Card quality is average tier score."""
        cards = [
            Card("Card1", CardType.ATTACK, 1, Rarity.COMMON, tier_score=80),
            Card("Card2", CardType.ATTACK, 1, Rarity.COMMON, tier_score=90),
            Card("Card3", CardType.ATTACK, 1, Rarity.COMMON, tier_score=70),
        ]
        
        deck = DeckEvaluation(cards=cards)
        quality = deck.calculate_card_quality()
        
        assert quality == 80.0  # (80 + 90 + 70) / 3
    
    def test_calculate_card_quality_empty(self):
        """Empty deck has zero quality."""
        deck = DeckEvaluation(cards=[])
        quality = deck.calculate_card_quality()
        
        assert quality == 0.0
    
    def test_calculate_synergy_coherence(self):
        """Synergy coherence measures card interactions."""
        cards = [
            Card("Heavy Blade", CardType.ATTACK, 2, Rarity.COMMON,
                 fusion_tags=["Strength-scaling"]),
            Card("Inflame", CardType.POWER, 1, Rarity.UNCOMMON,
                 fusion_tags=["Strength-scaling"]),
            Card("Strike", CardType.ATTACK, 1, Rarity.BASIC),
        ]
        
        deck = DeckEvaluation(cards=cards)
        synergy = deck.calculate_synergy_coherence()
        
        # At least 2 cards share Strength-scaling tag
        assert synergy > 0
    
    def test_calculate_curve_smoothness(self):
        """Curve smoothness evaluates mana distribution."""
        cards = [
            Card(f"Cost0_{i}", CardType.ATTACK, 0, Rarity.COMMON) for i in range(2)
        ] + [
            Card(f"Cost1_{i}", CardType.ATTACK, 1, Rarity.COMMON) for i in range(8)
        ] + [
            Card(f"Cost2_{i}", CardType.ATTACK, 2, Rarity.COMMON) for i in range(7)
        ] + [
            Card(f"Cost3_{i}", CardType.ATTACK, 3, Rarity.COMMON) for i in range(3)
        ]
        
        deck = DeckEvaluation(cards=cards)
        curve = deck.calculate_curve_smoothness()
        
        # Should have reasonable curve score
        assert 0 <= curve <= 100
    
    def test_calculate_consistency(self):
        """Consistency evaluates deck size and redundancy."""
        # Ideal size deck (30 cards)
        cards = [
            Card(f"Card{i}", CardType.ATTACK, 1, Rarity.COMMON) for i in range(30)
        ]
        
        deck = DeckEvaluation(cards=cards)
        consistency = deck.calculate_consistency()
        
        # Should score reasonably high for ideal size
        assert consistency >= 70
    
    def test_calculate_relic_impact(self):
        """Relic impact evaluates relic synergies."""
        cards = [
            Card("Heavy Blade", CardType.ATTACK, 2, Rarity.COMMON,
                 fusion_tags=["Strength-scaling"]),
        ]
        
        relics = [
            Relic("Vajra", RelicRarity.BOSS, "Gain 1 Strength",
                  synergies=["Strength-scaling"], tier_score=85.0),
        ]
        
        deck = DeckEvaluation(cards=cards, relics=relics)
        impact = deck.calculate_relic_impact()
        
        # Should score high due to synergy
        assert impact > 50
    
    def test_calculate_score(self):
        """Overall score uses composite formula."""
        cards = [
            Card(f"Card{i}", CardType.ATTACK, 1, Rarity.COMMON, tier_score=75)
            for i in range(30)
        ]
        
        deck = DeckEvaluation(cards=cards)
        score = deck.calculate_score()
        
        # Score should be in valid range
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_get_breakdown(self):
        """Breakdown provides all component scores."""
        cards = [
            Card("Card1", CardType.ATTACK, 1, Rarity.COMMON, tier_score=80),
            Card("Card2", CardType.ATTACK, 1, Rarity.COMMON, tier_score=80),
        ]
        
        deck = DeckEvaluation(cards=cards, name="Test")
        breakdown = deck.get_breakdown()
        
        assert "card_quality" in breakdown
        assert "synergy_coherence" in breakdown
        assert "curve_smoothness" in breakdown
        assert "consistency" in breakdown
        assert "relic_impact" in breakdown
        assert "overall_score" in breakdown
        assert "deck_size" in breakdown
        assert breakdown["deck_size"] == 2
    
    def test_to_dict(self):
        """Deck can be converted to dictionary."""
        cards = [
            Card("Strike", CardType.ATTACK, 1, Rarity.BASIC),
        ]
        
        deck = DeckEvaluation(cards=cards, name="Test Deck")
        deck_dict = deck.to_dict()
        
        assert deck_dict["name"] == "Test Deck"
        assert "cards" in deck_dict
        assert "evaluation" in deck_dict
        assert len(deck_dict["cards"]) == 1
