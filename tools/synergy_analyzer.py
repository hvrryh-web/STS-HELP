#!/usr/bin/env python3
"""
Synergy Analyzer for Slay the Spire

This tool analyzes potential synergies between cards and relics to help players
make informed deck-building decisions. It uses pattern matching and heuristic
rules to identify powerful combinations.

Based on research findings from STS strategy documentation.
"""

import json
import os
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class SynergyAnalyzer:
    """Analyzes card and relic synergies for Slay the Spire deck building."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the analyzer with game data.
        
        Args:
            data_dir: Path to data directory containing card and relic JSONs
        """
        if data_dir is None:
            # Default to ../data from this script's location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(script_dir), 'data')
        
        self.data_dir = data_dir
        self.cards = self._load_cards()
        self.relics = self._load_relics()
        self.synergy_rules = self._define_synergy_rules()
        
    def _load_cards(self) -> Dict[str, Dict]:
        """Load all card data from JSON files."""
        cards = {}
        cards_dir = os.path.join(self.data_dir, 'cards')
        
        for filename in ['ironclad_cards.json', 'silent_cards.json', 
                        'defect_cards.json', 'watcher_cards.json']:
            filepath = os.path.join(cards_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    character_cards = json.load(f)
                    cards.update(character_cards)
        
        return cards
    
    def _load_relics(self) -> Dict[str, Dict]:
        """Load all relic data from JSON file."""
        relics_file = os.path.join(self.data_dir, 'relics', 'relics.json')
        
        if os.path.exists(relics_file):
            with open(relics_file, 'r') as f:
                relic_data = json.load(f)
                # Flatten all relic categories
                all_relics = {}
                for category in relic_data.values():
                    all_relics.update(category)
                return all_relics
        
        return {}
    
    def _define_synergy_rules(self) -> List[Dict]:
        """Define synergy rules based on game mechanics and strategy research.
        
        These rules are derived from expert play analysis and research papers.
        """
        return [
            {
                'name': 'Exhaust Synergy',
                'description': 'Cards/relics that benefit from exhausting cards',
                'card_keywords': ['exhaust'],
                'relic_keywords': ['exhaust'],
                'examples': ['Dead Branch + Corruption', 'Feel No Pain + Exhaust cards']
            },
            {
                'name': 'Strength Scaling',
                'description': 'Cards that scale with Strength stat',
                'card_keywords': ['strength', 'heavy blade', 'sword boomerang'],
                'relic_keywords': ['strength', 'vajra', 'girya'],
                'examples': ['Demon Form + Heavy Blade', 'Limit Break + High-hit attacks']
            },
            {
                'name': 'Poison Synergy',
                'description': 'Cards that apply or amplify Poison',
                'card_keywords': ['poison', 'catalyst'],
                'relic_keywords': ['poison', 'snecko skull'],
                'examples': ['Catalyst + Noxious Fumes', 'Bouncing Flask + Catalyst']
            },
            {
                'name': 'Shiv Generation',
                'description': 'Cards that generate or benefit from Shivs',
                'card_keywords': ['shiv'],
                'relic_keywords': ['shiv', 'kunai', 'shuriken', 'ornamental fan'],
                'examples': ['Accuracy + Blade Dance', 'After Image + Shiv generation']
            },
            {
                'name': 'Orb Synergy',
                'description': 'Cards/relics that interact with Orbs',
                'card_keywords': ['orb', 'channel', 'evoke', 'focus'],
                'relic_keywords': ['orb', 'capacitor', 'focus'],
                'examples': ['Defragment + Lightning', 'Frost Orbs + Glacier']
            },
            {
                'name': 'Block Retention',
                'description': 'Retaining block across turns',
                'card_keywords': ['barricade', 'calipers'],
                'relic_keywords': ['barricade', 'calipers'],
                'examples': ['Barricade + Body Slam', 'Entrench + Calipers']
            },
            {
                'name': 'Stance Dancing',
                'description': 'Switching between Stances for benefits',
                'card_keywords': ['stance', 'calm', 'wrath', 'divinity'],
                'relic_keywords': ['stance', 'violet lotus'],
                'examples': ['Tantrum + Rushdown', 'Mental Fortress + Stance switching']
            },
            {
                'name': 'Energy Generation',
                'description': 'Cards/relics that provide extra energy',
                'card_keywords': ['energy'],
                'relic_keywords': ['energy'],
                'examples': ['Ice Cream + High-cost cards', 'Snecko Eye + Expensive cards']
            },
            {
                'name': 'Card Draw',
                'description': 'Increased card draw for consistency',
                'card_keywords': ['draw'],
                'relic_keywords': ['draw', 'card draw'],
                'examples': ['Acrobatics + Reflex', 'Bag of Preparation + Skill cards']
            },
            {
                'name': 'Discard Synergy',
                'description': 'Benefits from discarding cards',
                'card_keywords': ['discard', 'tactician', 'reflex'],
                'relic_keywords': ['discard', 'tough bandages', 'gambling chip'],
                'examples': ['Tactician + Discard cards', 'Eviscerate + Acrobatics']
            },
            {
                'name': '0-Cost Cards',
                'description': 'Benefits from playing many cards',
                'card_keywords': ['0-cost', 'free'],
                'relic_keywords': ['card played', 'nunchaku', 'pen nib'],
                'examples': ['Nunchaku + 0-cost attacks', 'Pen Nib + Shivs']
            },
        ]
    
    def analyze_deck(self, deck: List[str], relics: List[str]) -> Dict:
        """Analyze synergies in a given deck configuration.
        
        Args:
            deck: List of card names in the deck
            relics: List of relic names owned
            
        Returns:
            Dictionary containing synergy analysis results
        """
        # Count card types and keywords
        card_types = defaultdict(int)
        card_keywords = defaultdict(int)
        
        for card_name in deck:
            card_data = self.cards.get(card_name, {})
            card_type = card_data.get('type', 'Unknown')
            card_types[card_type] += 1
            
            # Extract keywords from description (simplified)
            description = card_data.get('description', '').lower()
            for keyword in ['exhaust', 'poison', 'strength', 'block', 'draw', 
                          'energy', 'shiv', 'orb', 'stance', 'discard']:
                if keyword in description:
                    card_keywords[keyword] += 1
        
        # Identify active synergies
        active_synergies = []
        for rule in self.synergy_rules:
            synergy_score = self._calculate_synergy_score(
                rule, deck, relics, card_keywords
            )
            if synergy_score > 0:
                active_synergies.append({
                    'name': rule['name'],
                    'description': rule['description'],
                    'score': synergy_score,
                    'examples': rule['examples']
                })
        
        # Sort by score
        active_synergies.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'deck_size': len(deck),
            'card_types': dict(card_types),
            'active_synergies': active_synergies,
            'relic_count': len(relics),
            'recommendations': self._generate_recommendations(
                active_synergies, card_types, deck, relics
            )
        }
    
    def _calculate_synergy_score(self, rule: Dict, deck: List[str], 
                                 relics: List[str], card_keywords: Dict) -> float:
        """Calculate how strongly a synergy rule applies to this deck.
        
        Args:
            rule: Synergy rule definition
            deck: List of card names
            relics: List of relic names
            card_keywords: Keyword counts from cards
            
        Returns:
            Synergy score (0 = no synergy, higher = stronger synergy)
        """
        score = 0.0
        
        # Check for relevant card keywords
        for keyword in rule.get('card_keywords', []):
            if keyword in card_keywords:
                score += card_keywords[keyword] * 1.0
        
        # Check for relevant relics
        for keyword in rule.get('relic_keywords', []):
            for relic in relics:
                relic_data = self.relics.get(relic, {})
                relic_desc = relic_data.get('description', '').lower()
                if keyword.lower() in relic_desc or keyword.lower() in relic.lower():
                    score += 3.0  # Relics are powerful enablers
        
        # Check for specific card names in examples
        for example in rule.get('examples', []):
            example_lower = example.lower()
            for card in deck:
                if card.lower() in example_lower:
                    score += 2.0
            for relic in relics:
                if relic.lower() in example_lower:
                    score += 2.0
        
        return score
    
    def _generate_recommendations(self, synergies: List[Dict], 
                                 card_types: Dict, deck: List[str],
                                 relics: List[str]) -> List[str]:
        """Generate strategic recommendations based on deck analysis.
        
        Args:
            synergies: Active synergies detected
            card_types: Count of each card type
            deck: Current deck
            relics: Current relics
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for strong synergies
        if synergies and synergies[0]['score'] > 5:
            recommendations.append(
                f"Strong synergy detected: {synergies[0]['name']}. "
                f"Continue building around this archetype."
            )
        
        # Check deck size
        if len(deck) > 35:
            recommendations.append(
                "Large deck detected. Consider removing weak cards for consistency."
            )
        elif len(deck) < 20:
            recommendations.append(
                "Small deck detected. Excellent for drawing key cards frequently."
            )
        
        # Check card type balance
        attacks = card_types.get('Attack', 0)
        skills = card_types.get('Skill', 0)
        powers = card_types.get('Power', 0)
        
        if attacks < 5:
            recommendations.append(
                "Low attack count. May struggle to deal damage efficiently."
            )
        if skills < 5:
            recommendations.append(
                "Low skill count. Consider adding defensive or utility cards."
            )
        if powers > 5:
            recommendations.append(
                "High power count. Be cautious of energy spent on setup."
            )
        
        # Check for multiple weaker synergies
        if len(synergies) > 3 and all(s['score'] < 4 for s in synergies):
            recommendations.append(
                "Multiple weak synergies detected. Consider focusing on one archetype."
            )
        
        return recommendations
    
    def find_best_additions(self, deck: List[str], relics: List[str],
                          available_cards: List[str], top_n: int = 5) -> List[Tuple[str, float]]:
        """Find the best cards to add to strengthen current synergies.
        
        Args:
            deck: Current deck
            relics: Current relics
            available_cards: List of cards available to add
            top_n: Number of top recommendations to return
            
        Returns:
            List of (card_name, synergy_score) tuples
        """
        current_analysis = self.analyze_deck(deck, relics)
        card_scores = []
        
        for card in available_cards:
            if card not in deck:  # Don't recommend duplicates unnecessarily
                # Analyze deck with this card added
                test_deck = deck + [card]
                test_analysis = self.analyze_deck(test_deck, relics)
                
                # Calculate improvement in synergy scores
                current_total = sum(s['score'] for s in current_analysis['active_synergies'])
                test_total = sum(s['score'] for s in test_analysis['active_synergies'])
                
                improvement = test_total - current_total
                card_scores.append((card, improvement))
        
        # Sort by improvement
        card_scores.sort(key=lambda x: x[1], reverse=True)
        
        return card_scores[:top_n]


def main():
    """Example usage of the Synergy Analyzer."""
    print("=== Slay the Spire Synergy Analyzer ===\n")
    
    # Initialize analyzer
    analyzer = SynergyAnalyzer()
    
    # Example Ironclad deck (Strength scaling)
    example_deck = [
        'Strike', 'Strike', 'Strike', 'Strike', 'Strike',
        'Defend', 'Defend', 'Defend', 'Defend',
        'Bash', 'Heavy Blade', 'Demon Form', 'Limit Break',
        'Inflame', 'Spot Weakness', 'Pommel Strike'
    ]
    
    example_relics = ['Burning Blood', 'Vajra', 'Girya', 'Bag of Marbles']
    
    print("Analyzing deck:")
    print(f"Cards: {len(example_deck)}")
    print(f"Relics: {', '.join(example_relics)}\n")
    
    # Analyze the deck
    analysis = analyzer.analyze_deck(example_deck, example_relics)
    
    print(f"Deck Size: {analysis['deck_size']}")
    print(f"Card Types: {analysis['card_types']}\n")
    
    print("Active Synergies:")
    for synergy in analysis['active_synergies']:
        print(f"  - {synergy['name']} (Score: {synergy['score']:.1f})")
        print(f"    {synergy['description']}")
        print(f"    Examples: {', '.join(synergy['examples'][:2])}")
        print()
    
    if analysis['recommendations']:
        print("Recommendations:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")
        print()
    
    # Example: Find best cards to add
    potential_additions = ['Sword Boomerang', 'Twin Strike', 'Battle Trance', 
                          'Seeing Red', 'Clothesline']
    
    print("Best cards to add:")
    best_cards = analyzer.find_best_additions(example_deck, example_relics, 
                                             potential_additions, top_n=3)
    for card, score in best_cards:
        print(f"  • {card}: +{score:.1f} synergy improvement")


if __name__ == '__main__':
    main()
