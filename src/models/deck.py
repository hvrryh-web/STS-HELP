"""
Deck evaluation model for Slay the Spire.

This module implements the composite scoring formula:
Score = 0.4Q + 0.25S + 0.15C + 0.10K + 0.10R

Where:
    Q = Card Quality (average tier score)
    S = Synergy Coherence (synergy density)
    C = Curve Smoothness (mana curve distribution)
    K = Consistency (deck size and redundancy)
    R = Relic Impact (relic synergy with deck)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import statistics

from .card import Card
from .relic import Relic


@dataclass
class DeckEvaluation:
    """
    Deck evaluation with composite scoring.
    
    Attributes:
        cards: List of cards in the deck
        relics: List of relics
        name: Deck archetype name
        character: Character this deck is for
    """
    cards: List[Card]
    relics: List[Relic] = field(default_factory=list)
    name: str = "Unnamed Deck"
    character: str = "Ironclad"
    
    def calculate_card_quality(self) -> float:
        """
        Calculate Q: Card Quality score.
        
        Returns average tier score of all cards in the deck.
        
        Returns:
            Quality score (0-100)
        """
        if not self.cards:
            return 0.0
        
        tier_scores = [card.tier_score for card in self.cards]
        return statistics.mean(tier_scores)
    
    def calculate_synergy_coherence(self) -> float:
        """
        Calculate S: Synergy Coherence score.
        
        Measures how well cards work together by counting synergy matches.
        
        Returns:
            Synergy score (0-100)
        """
        if not self.cards or len(self.cards) < 2:
            return 0.0
        
        # Count synergy tags across all cards
        all_tags = []
        for card in self.cards:
            all_tags.extend(card.fusion_tags)
            all_tags.extend(card.function_tags)
        
        if not all_tags:
            return 50.0  # Neutral score if no tags
        
        # Count synergy matches
        synergy_count = 0
        total_possible = len(self.cards) * (len(self.cards) - 1) // 2
        
        for i, card1 in enumerate(self.cards):
            for card2 in self.cards[i+1:]:
                # Check if cards share synergy tags
                tags1 = set(card1.fusion_tags + card1.function_tags)
                tags2 = set(card2.fusion_tags + card2.function_tags)
                if tags1.intersection(tags2):
                    synergy_count += 1
        
        # Calculate synergy density
        if total_possible > 0:
            synergy_density = (synergy_count / total_possible) * 100
        else:
            synergy_density = 0.0
        
        return min(synergy_density, 100.0)
    
    def calculate_curve_smoothness(self) -> float:
        """
        Calculate C: Curve Smoothness score.
        
        Evaluates mana curve distribution. Ideal curve has cards at costs 0-3.
        
        Returns:
            Curve score (0-100)
        """
        if not self.cards:
            return 0.0
        
        # Count cards by cost
        cost_distribution = {}
        for card in self.cards:
            cost = card.cost
            if cost == -1:  # X-cost cards
                cost = 1  # Treat as cost 1 for curve purposes
            cost = min(cost, 5)  # Cap at 5+ for distribution
            cost_distribution[cost] = cost_distribution.get(cost, 0) + 1
        
        # Ideal distribution: some 0-cost, many 1-2 cost, fewer 3+ cost
        # Score based on presence across cost range
        ideal_distribution = {0: 0.1, 1: 0.35, 2: 0.30, 3: 0.15, 4: 0.05, 5: 0.05}
        
        total_cards = len(self.cards)
        score = 0.0
        
        for cost, ideal_fraction in ideal_distribution.items():
            actual_fraction = cost_distribution.get(cost, 0) / total_cards
            # Penalize deviation from ideal
            deviation = abs(actual_fraction - ideal_fraction)
            score += (1 - deviation) * 100 / len(ideal_distribution)
        
        return min(score, 100.0)
    
    def calculate_consistency(self) -> float:
        """
        Calculate K: Consistency score.
        
        Evaluates deck size and card redundancy. Smaller, focused decks score higher.
        
        Returns:
            Consistency score (0-100)
        """
        if not self.cards:
            return 0.0
        
        deck_size = len(self.cards)
        
        # Ideal deck size is 25-35 cards
        if 25 <= deck_size <= 35:
            size_score = 100.0
        elif deck_size < 25:
            # Too small - linear penalty
            size_score = max(0, 100 - (25 - deck_size) * 5)
        else:
            # Too large - linear penalty
            size_score = max(0, 100 - (deck_size - 35) * 3)
        
        # Calculate redundancy (duplicate cards)
        card_counts = {}
        for card in self.cards:
            card_counts[card.name] = card_counts.get(card.name, 0) + 1
        
        # Some redundancy is good (2-3 copies of key cards)
        redundancy_score = 0.0
        for count in card_counts.values():
            if count == 2 or count == 3:
                redundancy_score += 10
            elif count > 3:
                redundancy_score -= 5  # Too many copies
        
        redundancy_score = max(0, min(redundancy_score, 50))
        
        return (size_score * 0.7 + redundancy_score * 0.3)
    
    def calculate_relic_impact(self) -> float:
        """
        Calculate R: Relic Impact score.
        
        Evaluates how well relics synergize with the deck.
        
        Returns:
            Relic impact score (0-100)
        """
        if not self.relics:
            return 50.0  # Neutral score if no relics
        
        # Get average relic value
        relic_quality = statistics.mean([relic.tier_score for relic in self.relics])
        
        # Check for synergies between relics and cards
        synergy_count = 0
        total_checks = len(self.relics) * len(self.cards)
        
        for relic in self.relics:
            for card in self.cards:
                # Check if relic synergizes with card tags
                card_tags = set(card.fusion_tags + card.function_tags)
                relic_tags = set(relic.synergies)
                if card_tags.intersection(relic_tags):
                    synergy_count += 1
        
        if total_checks > 0:
            synergy_ratio = synergy_count / total_checks
        else:
            synergy_ratio = 0.0
        
        # Combine relic quality and synergy
        return min(relic_quality * 0.6 + synergy_ratio * 100 * 0.4, 100.0)
    
    def calculate_score(self) -> float:
        """
        Calculate overall deck score using composite formula.
        
        Score = 0.4Q + 0.25S + 0.15C + 0.10K + 0.10R
        
        Returns:
            Overall deck score (0-100)
        """
        Q = self.calculate_card_quality()
        S = self.calculate_synergy_coherence()
        C = self.calculate_curve_smoothness()
        K = self.calculate_consistency()
        R = self.calculate_relic_impact()
        
        score = 0.4 * Q + 0.25 * S + 0.15 * C + 0.10 * K + 0.10 * R
        
        return round(score, 1)
    
    def get_breakdown(self) -> Dict[str, float]:
        """
        Get detailed breakdown of all score components.
        
        Returns:
            Dictionary with all component scores and overall score
        """
        Q = self.calculate_card_quality()
        S = self.calculate_synergy_coherence()
        C = self.calculate_curve_smoothness()
        K = self.calculate_consistency()
        R = self.calculate_relic_impact()
        
        return {
            "card_quality": round(Q, 1),
            "synergy_coherence": round(S, 1),
            "curve_smoothness": round(C, 1),
            "consistency": round(K, 1),
            "relic_impact": round(R, 1),
            "overall_score": self.calculate_score(),
            "deck_size": len(self.cards),
            "relic_count": len(self.relics),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert deck evaluation to dictionary representation."""
        return {
            "name": self.name,
            "character": self.character,
            "cards": [card.to_dict() for card in self.cards],
            "relics": [relic.to_dict() for relic in self.relics],
            "evaluation": self.get_breakdown(),
        }
