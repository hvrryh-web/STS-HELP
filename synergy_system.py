"""
Synergy detection system for Slay the Spire simulation.

Provides deck composition analysis and synergy calculation.
Resolution for E2: No deck synergy modeling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum

from engine_common import Card, CardType


class Archetype(Enum):
    """Deck archetype classifications."""
    STRENGTH = "strength"
    BLOCK = "block"
    EXHAUST = "exhaust"
    POISON = "poison"
    SHIV = "shiv"
    ORB = "orb"
    FOCUS = "focus"
    STANCE = "stance"
    MANTRA = "mantra"
    WRATH = "wrath"
    CALM = "calm"
    DISCARD = "discard"
    DRAW = "draw"
    ENERGY = "energy"


@dataclass
class SynergyPair:
    """
    A synergy between two cards.
    
    Attributes:
        card_a: First card name.
        card_b: Second card name.
        bonus: Synergy bonus multiplier.
        archetype: What archetype this synergy belongs to.
        description: Human-readable description.
    """
    card_a: str
    card_b: str
    bonus: float
    archetype: Archetype
    description: str = ""


# Predefined synergy pairs for each character
IRONCLAD_SYNERGIES: List[SynergyPair] = [
    # Strength synergies
    SynergyPair("Limit Break", "Heavy Blade", 2.5, Archetype.STRENGTH,
                "Limit Break doubles strength, Heavy Blade multiplies strength 3-5x"),
    SynergyPair("Limit Break", "Sword Boomerang", 2.0, Archetype.STRENGTH,
                "Multi-hit attack benefits from doubled strength"),
    SynergyPair("Demon Form", "Heavy Blade", 2.0, Archetype.STRENGTH,
                "Scaling strength + strength multiplier"),
    SynergyPair("Inflame", "Heavy Blade", 1.5, Archetype.STRENGTH,
                "Strength gain + strength multiplier"),
    SynergyPair("Spot Weakness", "Heavy Blade", 1.5, Archetype.STRENGTH,
                "Conditional strength + strength multiplier"),
    SynergyPair("Limit Break", "Demon Form", 1.8, Archetype.STRENGTH,
                "Double scaling strength"),
    SynergyPair("Flex", "Heavy Blade", 1.3, Archetype.STRENGTH,
                "Temporary strength + multiplier for burst"),
    
    # Block/defense synergies
    SynergyPair("Barricade", "Body Slam", 2.5, Archetype.BLOCK,
                "Retained block becomes damage"),
    SynergyPair("Barricade", "Entrench", 2.0, Archetype.BLOCK,
                "Retained block doubled each turn"),
    SynergyPair("Entrench", "Body Slam", 1.8, Archetype.BLOCK,
                "Doubled block for damage"),
    SynergyPair("Metallicize", "Body Slam", 1.5, Archetype.BLOCK,
                "Consistent block + block-based damage"),
    SynergyPair("Impervious", "Body Slam", 1.5, Archetype.BLOCK,
                "Big block burst + damage conversion"),
    
    # Exhaust synergies
    SynergyPair("Corruption", "Feel No Pain", 3.0, Archetype.EXHAUST,
                "Free skills + block per exhaust"),
    SynergyPair("Corruption", "Dark Embrace", 2.5, Archetype.EXHAUST,
                "Free skills + draw per exhaust"),
    SynergyPair("Dead Branch", "Feel No Pain", 2.0, Archetype.EXHAUST,
                "Random cards + block per exhaust"),
    SynergyPair("Corruption", "Dead Branch", 3.5, Archetype.EXHAUST,
                "Free skills become random cards"),
    SynergyPair("Feel No Pain", "Dark Embrace", 1.5, Archetype.EXHAUST,
                "Block + draw per exhaust"),
    SynergyPair("Second Wind", "Feel No Pain", 1.8, Archetype.EXHAUST,
                "Mass exhaust + block synergy"),
    SynergyPair("Fiend Fire", "Feel No Pain", 1.5, Archetype.EXHAUST,
                "Hand exhaust + block"),
    
    # Self-damage synergies
    SynergyPair("Rupture", "Offering", 1.8, Archetype.STRENGTH,
                "Strength on HP loss + HP loss for draw/energy"),
    SynergyPair("Rupture", "Brutality", 1.5, Archetype.STRENGTH,
                "Strength per turn from HP loss"),
    SynergyPair("Rupture", "Hemokinesis", 1.3, Archetype.STRENGTH,
                "Strength from attack's HP cost"),
]

SILENT_SYNERGIES: List[SynergyPair] = [
    # Poison synergies
    SynergyPair("Catalyst", "Noxious Fumes", 2.5, Archetype.POISON,
                "Double/triple poison per turn"),
    SynergyPair("Catalyst", "Deadly Poison", 2.0, Archetype.POISON,
                "Double/triple large poison application"),
    SynergyPair("Corpse Explosion", "Catalyst", 2.5, Archetype.POISON,
                "Poison explosion + poison multiplier"),
    SynergyPair("Envenom", "Blade Dance", 1.8, Archetype.POISON,
                "Poison per attack + many attacks"),
    SynergyPair("Snecko Skull", "Noxious Fumes", 1.5, Archetype.POISON,
                "Extra poison per application + consistent poison"),
    
    # Shiv synergies
    SynergyPair("Accuracy", "Blade Dance", 2.5, Archetype.SHIV,
                "Shiv damage bonus + shiv generation"),
    SynergyPair("Accuracy", "Cloak and Dagger", 2.0, Archetype.SHIV,
                "Shiv damage + shiv generation with block"),
    SynergyPair("After Image", "Blade Dance", 2.0, Archetype.SHIV,
                "Block per card + many cards played"),
    SynergyPair("Finisher", "Blade Dance", 1.8, Archetype.SHIV,
                "Damage per attack + many attacks"),
    SynergyPair("Accuracy", "Infinite Blades", 2.0, Archetype.SHIV,
                "Shiv damage + consistent shiv generation"),
    SynergyPair("Kunai", "Blade Dance", 1.5, Archetype.SHIV,
                "Dexterity from attacks + many attacks"),
    SynergyPair("Shuriken", "Blade Dance", 1.5, Archetype.SHIV,
                "Strength from attacks + many attacks"),
    
    # Discard synergies
    SynergyPair("Tingsha", "Calculated Gamble", 1.8, Archetype.DISCARD,
                "Damage on discard + mass discard"),
    SynergyPair("Tough Bandages", "Survivor", 1.5, Archetype.DISCARD,
                "Block on discard + discard skill"),
    SynergyPair("Tactician", "Survivor", 1.5, Archetype.DISCARD,
                "Energy on discard + discard skill"),
    SynergyPair("Reflex", "Calculated Gamble", 1.5, Archetype.DISCARD,
                "Draw when discarded + mass discard"),
]

DEFECT_SYNERGIES: List[SynergyPair] = [
    # Orb/Focus synergies
    SynergyPair("Defragment", "Loop", 2.0, Archetype.FOCUS,
                "Focus + orb triggering"),
    SynergyPair("Consume", "Defragment", 1.8, Archetype.FOCUS,
                "Slot removal for focus + focus gain"),
    SynergyPair("Biased Cognition", "Orange Pellets", 2.5, Archetype.FOCUS,
                "Focus gain without debuff removal"),
    SynergyPair("Capacitor", "Loop", 1.5, Archetype.ORB,
                "More orb slots + orb triggering"),
    
    # Lightning synergies
    SynergyPair("Electrodynamics", "Defragment", 1.8, Archetype.ORB,
                "All enemy lightning + focus"),
    SynergyPair("Thunder Strike", "Storm", 2.0, Archetype.ORB,
                "Damage per lightning channeled + lightning on power"),
    
    # Frost synergies
    SynergyPair("Glacier", "Loop", 1.5, Archetype.ORB,
                "Frost generation + orb triggering"),
    SynergyPair("Cold Snap", "Defragment", 1.3, Archetype.ORB,
                "Frost + focus for more block"),
    
    # Dark synergies
    SynergyPair("Recursion", "Darkness", 1.5, Archetype.ORB,
                "Orb repositioning + dark orb growth"),
    
    # Echo/power synergies
    SynergyPair("Echo Form", "Meteor Strike", 2.5, Archetype.ENERGY,
                "Double expensive attack"),
    SynergyPair("Creative AI", "Mummified Hand", 2.0, Archetype.ENERGY,
                "Power generation + cost reduction on power"),
    SynergyPair("All for One", "Claw", 2.0, Archetype.ENERGY,
                "Retrieve 0-cost cards + scaling 0-cost attack"),
]

WATCHER_SYNERGIES: List[SynergyPair] = [
    # Stance synergies
    SynergyPair("Mental Fortress", "Rushdown", 2.5, Archetype.STANCE,
                "Block on stance change + draw on wrath"),
    SynergyPair("Flurry of Blows", "Empty Mind", 2.0, Archetype.STANCE,
                "Attack returns + calm exit"),
    SynergyPair("Flurry of Blows", "Rushdown", 1.8, Archetype.STANCE,
                "Attack returns + draw on wrath"),
    SynergyPair("Like Water", "Mental Fortress", 1.5, Archetype.STANCE,
                "Block in calm + block on change"),
    
    # Wrath synergies
    SynergyPair("Tantrum", "Ragnarok", 1.8, Archetype.WRATH,
                "Enter wrath + high damage multi-hit"),
    SynergyPair("Eruption", "Sands of Time", 1.5, Archetype.WRATH,
                "Wrath entry + scaling attack"),
    
    # Calm synergies
    SynergyPair("Fear No Evil", "Empty Mind", 1.5, Archetype.CALM,
                "Block in calm + calm exit draw"),
    SynergyPair("Inner Peace", "Halt", 1.3, Archetype.CALM,
                "Calm entry + block in calm"),
    
    # Mantra synergies
    SynergyPair("Devotion", "Brilliance", 2.0, Archetype.MANTRA,
                "Mantra generation + mantra-based damage"),
    SynergyPair("Worship", "Brilliance", 1.8, Archetype.MANTRA,
                "Large mantra gain + mantra damage"),
    SynergyPair("Prostrate", "Devotion", 1.5, Archetype.MANTRA,
                "Mantra + block with mantra generation"),
    
    # Retain synergies
    SynergyPair("Establishment", "Windmill Strike", 1.8, Archetype.DRAW,
                "Reduce retain cost + retain scaling attack"),
    SynergyPair("Meditate", "Sash Whip", 1.5, Archetype.STANCE,
                "Card retrieval + conditional weak"),
]

# Relic synergies (card + relic combinations)
RELIC_SYNERGIES: Dict[str, List[Tuple[str, float, str]]] = {
    # Ironclad
    "Dead Branch": [
        ("Corruption", 4.0, "Free skills become random cards"),
        ("Feel No Pain", 2.0, "Random cards + block per exhaust"),
        ("Second Wind", 2.0, "Mass exhaust + random cards"),
        ("True Grit", 1.5, "Exhaust + random card"),
        ("Fiend Fire", 2.0, "Hand exhaust + random cards"),
    ],
    "Shuriken": [
        ("Blade Dance", 2.0, "Strength from shivs"),
        ("Sword Boomerang", 1.5, "Multi-hit for counter"),
        ("Pummel", 1.8, "Many hits for counter"),
    ],
    "Kunai": [
        ("Blade Dance", 2.0, "Dexterity from shivs"),
        ("Sword Boomerang", 1.5, "Multi-hit for counter"),
    ],
    "Pen Nib": [
        ("Heavy Blade", 2.5, "Double damage on multiplied attack"),
        ("Whirlwind", 2.0, "Double damage on X-cost"),
        ("Bludgeon", 2.0, "Double already high damage"),
    ],
    "Snecko Eye": [
        ("Meteor Strike", 2.0, "Chance for 0-cost expensive card"),
        ("Demon Form", 1.8, "Potential 0-cost power"),
        ("Bludgeon", 2.0, "Chance for 0-cost high damage"),
    ],
    "Runic Pyramid": [
        ("Limit Break", 1.5, "Keep for setup turns"),
        ("Catalyst", 1.8, "Keep for poison buildup"),
    ],
    "Mummified Hand": [
        ("Creative AI", 2.5, "Powers generate powers cheaply"),
        ("Demon Form", 1.5, "Power reduces other costs"),
        ("Echo Form", 1.5, "Power reduces other costs"),
    ],
    "Ice Cream": [
        ("Offering", 1.8, "Energy carries over"),
        ("Whirlwind", 1.5, "Save for big X-cost"),
        ("Skewer", 1.5, "Save for big X-cost"),
    ],
    "Paper Frog": [
        ("Bash", 1.5, "Stronger vulnerable"),
        ("Uppercut", 1.5, "Stronger vulnerable"),
        ("Terror", 1.5, "Stronger vulnerable"),
    ],
}


class SynergyCalculator:
    """
    Calculates deck synergy scores.
    
    Provides methods for:
    - Computing total deck synergy
    - Evaluating synergy gain from adding a card
    - Detecting deck archetypes
    """
    
    def __init__(self):
        """Initialize synergy calculator with predefined synergies."""
        self.synergies: Dict[str, Dict[str, float]] = {}
        self.relic_synergies = RELIC_SYNERGIES
        
        # Build synergy lookup table
        all_synergies = (
            IRONCLAD_SYNERGIES + 
            SILENT_SYNERGIES + 
            DEFECT_SYNERGIES + 
            WATCHER_SYNERGIES
        )
        
        for syn in all_synergies:
            key_a = syn.card_a.lower()
            key_b = syn.card_b.lower()
            
            if key_a not in self.synergies:
                self.synergies[key_a] = {}
            if key_b not in self.synergies:
                self.synergies[key_b] = {}
            
            self.synergies[key_a][key_b] = syn.bonus
            self.synergies[key_b][key_a] = syn.bonus
    
    def calculate_deck_synergy(self, deck: List[str], relics: Optional[List[str]] = None) -> float:
        """
        Calculate total synergy score for a deck.
        
        Args:
            deck: List of card names in deck.
            relics: Optional list of relic names.
        
        Returns:
            Total synergy score.
        """
        total = 0.0
        deck_lower = [c.lower().rstrip('+') for c in deck]
        deck_set = set(deck_lower)
        
        # Card-card synergies
        for card_a in deck_set:
            if card_a in self.synergies:
                for card_b, bonus in self.synergies[card_a].items():
                    if card_b in deck_set and card_a < card_b:  # Avoid double counting
                        count_a = deck_lower.count(card_a)
                        count_b = deck_lower.count(card_b)
                        # Synergy scales with minimum of the two card counts
                        total += bonus * min(count_a, count_b)
        
        # Card-relic synergies
        if relics:
            relics_lower = [r.lower() for r in relics]
            for relic in relics_lower:
                if relic in self.relic_synergies:
                    for card_name, bonus, _ in self.relic_synergies[relic]:
                        card_key = card_name.lower()
                        if card_key in deck_set:
                            count = deck_lower.count(card_key)
                            total += bonus * count
        
        return total
    
    def evaluate_card_addition(
        self,
        deck: List[str],
        candidate: str,
        relics: Optional[List[str]] = None
    ) -> float:
        """
        Evaluate synergy gain from adding a card to deck.
        
        Args:
            deck: Current deck card names.
            candidate: Card to consider adding.
            relics: Optional list of relic names.
        
        Returns:
            Synergy value gain from adding the card.
        """
        current_synergy = self.calculate_deck_synergy(deck, relics)
        new_synergy = self.calculate_deck_synergy(deck + [candidate], relics)
        return new_synergy - current_synergy
    
    def get_synergy_pairs(self, card_name: str) -> List[Tuple[str, float]]:
        """
        Get all synergy pairs for a card.
        
        Args:
            card_name: Card name.
        
        Returns:
            List of (card_name, bonus) tuples.
        """
        key = card_name.lower().rstrip('+')
        if key in self.synergies:
            return list(self.synergies[key].items())
        return []
    
    def detect_archetypes(self, deck: List[str]) -> Dict[Archetype, float]:
        """
        Detect deck archetypes based on card composition.
        
        Args:
            deck: List of card names.
        
        Returns:
            Dictionary of archetype to strength score.
        """
        archetype_scores: Dict[Archetype, float] = {arch: 0.0 for arch in Archetype}
        deck_set = set(c.lower().rstrip('+') for c in deck)
        
        # Ironclad archetypes
        strength_cards = {'limit break', 'demon form', 'inflame', 'spot weakness', 
                          'heavy blade', 'sword boomerang', 'flex'}
        exhaust_cards = {'corruption', 'feel no pain', 'dark embrace', 'second wind',
                         'fiend fire', 'true grit', 'burning pact'}
        block_cards = {'barricade', 'entrench', 'body slam', 'impervious', 'metallicize'}
        
        archetype_scores[Archetype.STRENGTH] = len(deck_set & strength_cards) * 1.5
        archetype_scores[Archetype.EXHAUST] = len(deck_set & exhaust_cards) * 1.5
        archetype_scores[Archetype.BLOCK] = len(deck_set & block_cards) * 1.5
        
        # Silent archetypes
        poison_cards = {'catalyst', 'noxious fumes', 'deadly poison', 'corpse explosion',
                        'bouncing flask', 'crippling cloud', 'envenom'}
        shiv_cards = {'accuracy', 'blade dance', 'cloak and dagger', 'finisher',
                      'infinite blades', 'after image', 'storm of steel'}
        discard_cards = {'calculated gamble', 'survivor', 'tactician', 'reflex',
                         'eviscerate', 'sneaky strike'}
        
        archetype_scores[Archetype.POISON] = len(deck_set & poison_cards) * 1.5
        archetype_scores[Archetype.SHIV] = len(deck_set & shiv_cards) * 1.5
        archetype_scores[Archetype.DISCARD] = len(deck_set & discard_cards) * 1.5
        
        # Defect archetypes
        orb_cards = {'loop', 'consume', 'capacitor', 'glacier', 'cold snap',
                     'electrodynamics', 'thunder strike', 'recursion'}
        focus_cards = {'defragment', 'biased cognition', 'consume', 'core surge'}
        
        archetype_scores[Archetype.ORB] = len(deck_set & orb_cards) * 1.5
        archetype_scores[Archetype.FOCUS] = len(deck_set & focus_cards) * 1.5
        
        # Watcher archetypes
        stance_cards = {'mental fortress', 'rushdown', 'flurry of blows', 'like water',
                        'tantrum', 'fear no evil', 'inner peace'}
        mantra_cards = {'devotion', 'brilliance', 'worship', 'prostrate', 'blasphemy'}
        
        archetype_scores[Archetype.STANCE] = len(deck_set & stance_cards) * 1.5
        archetype_scores[Archetype.MANTRA] = len(deck_set & mantra_cards) * 1.5
        
        return {k: v for k, v in archetype_scores.items() if v > 0}
    
    def get_archetype_recommendations(
        self,
        deck: List[str],
        available_cards: List[str]
    ) -> List[Tuple[str, float, str]]:
        """
        Get card recommendations based on deck archetypes.
        
        Args:
            deck: Current deck card names.
            available_cards: Cards available to add.
        
        Returns:
            List of (card_name, synergy_gain, reason) tuples, sorted by synergy gain.
        """
        recommendations = []
        
        for card in available_cards:
            synergy_gain = self.evaluate_card_addition(deck, card)
            
            if synergy_gain > 0:
                pairs = self.get_synergy_pairs(card)
                deck_set = set(c.lower().rstrip('+') for c in deck)
                
                # Find which existing cards it synergizes with
                synergy_with = [p[0] for p in pairs if p[0] in deck_set]
                if synergy_with:
                    reason = f"Synergizes with: {', '.join(synergy_with[:3])}"
                else:
                    reason = "Potential future synergy"
                
                recommendations.append((card, synergy_gain, reason))
        
        return sorted(recommendations, key=lambda x: x[1], reverse=True)


# Global synergy calculator instance
_synergy_calculator: Optional[SynergyCalculator] = None


def get_synergy_calculator() -> SynergyCalculator:
    """Get the global synergy calculator instance."""
    global _synergy_calculator
    if _synergy_calculator is None:
        _synergy_calculator = SynergyCalculator()
    return _synergy_calculator


def calculate_synergy(deck: List[str], relics: Optional[List[str]] = None) -> float:
    """
    Convenience function to calculate deck synergy.
    
    Args:
        deck: List of card names.
        relics: Optional list of relic names.
    
    Returns:
        Total synergy score.
    """
    return get_synergy_calculator().calculate_deck_synergy(deck, relics)
