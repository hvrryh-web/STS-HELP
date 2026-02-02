"""
Data-driven card loading system.

Loads cards from JSON definitions instead of hardcoded Python.
Supports composable card effects for flexible card implementation.

Resolution for G1: Incomplete card effect modeling.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

from engine_common import Card, CardType


class EffectType(Enum):
    """Types of card effects."""
    DAMAGE = "damage"
    BLOCK = "block"
    DRAW = "draw"
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    VULNERABLE = "vulnerable"
    WEAK = "weak"
    POISON = "poison"
    ENERGY = "energy"
    EXHAUST = "exhaust"
    DOUBLE_STRENGTH = "double_strength"
    CHANNEL = "channel"
    EVOKE = "evoke"
    STANCE = "stance"
    HEAL = "heal"
    MAX_HP = "max_hp"
    HP_LOSS = "hp_loss"
    STRENGTH_PER_TURN = "strength_per_turn"
    RETAIN_BLOCK = "retain_block"
    THORNS = "thorns"


@dataclass
class CardEffect:
    """
    Composable card effect.
    
    Attributes:
        effect_type: Type of effect.
        value: Numeric value for the effect.
        target: Target of the effect (enemy, self, all_enemies, random).
        scaling: What stat the effect scales with (strength, dexterity, focus).
        multiplier: Multiplier for scaling (e.g., Heavy Blade = 3x strength).
        condition: When the effect applies (always, if_vulnerable, stance_wrath, etc.).
        hits: Number of hits for multi-hit attacks.
    """
    effect_type: EffectType
    value: int = 0
    target: str = "enemy"
    scaling: str = "none"
    multiplier: float = 1.0
    condition: str = "always"
    hits: int = 1


@dataclass
class LoadedCard:
    """
    A card loaded from JSON with full effect information.
    
    Attributes:
        name: Card name.
        cost: Energy cost (can be -1 for X-cost cards).
        card_type: Type of card.
        rarity: Card rarity.
        character: Character this card belongs to.
        effects: List of card effects.
        upgraded_effects: List of effects when upgraded.
        keywords: List of keywords (e.g., exhaust, ethereal).
        synergies: List of synergy tags.
        description: Card description text.
    """
    name: str
    cost: int
    card_type: CardType
    rarity: str = "Common"
    character: str = ""
    effects: List[CardEffect] = field(default_factory=list)
    upgraded_effects: List[CardEffect] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    synergies: List[str] = field(default_factory=list)
    description: str = ""
    
    def to_engine_card(self, upgraded: bool = False) -> Card:
        """
        Convert to engine Card format.
        
        Args:
            upgraded: Whether to use upgraded effects.
        
        Returns:
            Card instance for use in simulation.
        """
        effects_dict = {}
        
        effect_list = self.upgraded_effects if upgraded and self.upgraded_effects else self.effects
        
        for effect in effect_list:
            if effect.effect_type == EffectType.DAMAGE:
                effects_dict['damage'] = effect.value
                if effect.hits > 1:
                    effects_dict['hits'] = effect.hits
                if effect.multiplier != 1.0:
                    effects_dict['strength_multiplier'] = int(effect.multiplier)
                if effect.target != "enemy":
                    effects_dict['target'] = effect.target
            elif effect.effect_type == EffectType.BLOCK:
                effects_dict['block'] = effect.value
            elif effect.effect_type == EffectType.DRAW:
                effects_dict['draw'] = effect.value
            elif effect.effect_type == EffectType.STRENGTH:
                effects_dict['strength'] = effect.value
            elif effect.effect_type == EffectType.DEXTERITY:
                effects_dict['dexterity'] = effect.value
            elif effect.effect_type == EffectType.VULNERABLE:
                effects_dict['vulnerable'] = effect.value
            elif effect.effect_type == EffectType.WEAK:
                effects_dict['weak'] = effect.value
            elif effect.effect_type == EffectType.POISON:
                effects_dict['poison'] = effect.value
            elif effect.effect_type == EffectType.ENERGY:
                effects_dict['energy'] = effect.value
            elif effect.effect_type == EffectType.DOUBLE_STRENGTH:
                effects_dict['double_strength'] = True
            elif effect.effect_type == EffectType.CHANNEL:
                effects_dict['channel'] = effect.target  # orb type
            elif effect.effect_type == EffectType.EVOKE:
                effects_dict['evoke'] = effect.value
            elif effect.effect_type == EffectType.STANCE:
                effects_dict['enter_stance'] = effect.target
            elif effect.effect_type == EffectType.HEAL:
                effects_dict['heal'] = effect.value
            elif effect.effect_type == EffectType.HP_LOSS:
                effects_dict['hp_loss'] = effect.value
            elif effect.effect_type == EffectType.STRENGTH_PER_TURN:
                effects_dict['strength_per_turn'] = effect.value
            elif effect.effect_type == EffectType.RETAIN_BLOCK:
                effects_dict['retain_block'] = True
            elif effect.effect_type == EffectType.THORNS:
                effects_dict['thorns'] = effect.value
        
        return Card(
            name=self.name + ("+" if upgraded else ""),
            cost=self.cost,
            card_type=self.card_type,
            effects=effects_dict,
            upgraded=upgraded,
            exhaust='exhaust' in self.keywords,
            ethereal='ethereal' in self.keywords,
            innate='innate' in self.keywords
        )


class CardLoader:
    """
    Loads cards from JSON definition files.
    
    Provides centralized card management with caching.
    """
    
    def __init__(self, data_dir: str = "data/cards"):
        """
        Initialize card loader.
        
        Args:
            data_dir: Path to card data directory.
        """
        self.data_dir = Path(data_dir)
        self._cache: Dict[str, LoadedCard] = {}
        self._loaded = False
    
    def _parse_card_type(self, type_str: str) -> CardType:
        """Parse card type string to CardType enum."""
        type_map = {
            'attack': CardType.ATTACK,
            'skill': CardType.SKILL,
            'power': CardType.POWER,
            'status': CardType.STATUS,
            'curse': CardType.CURSE
        }
        return type_map.get(type_str.lower(), CardType.ATTACK)
    
    def _parse_effects(self, effects_dict: Dict[str, Any]) -> List[CardEffect]:
        """Parse effects dictionary into CardEffect list."""
        effects = []
        
        if 'damage' in effects_dict:
            effect = CardEffect(
                effect_type=EffectType.DAMAGE,
                value=effects_dict['damage'],
                hits=effects_dict.get('hits', 1),
                multiplier=effects_dict.get('strength_multiplier', 1.0),
                target=effects_dict.get('target', 'enemy')
            )
            effects.append(effect)
        
        if 'block' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.BLOCK,
                value=effects_dict['block']
            ))
        
        if 'draw' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.DRAW,
                value=effects_dict['draw']
            ))
        
        if 'strength' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.STRENGTH,
                value=effects_dict['strength']
            ))
        
        if 'strength_per_turn' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.STRENGTH_PER_TURN,
                value=effects_dict['strength_per_turn']
            ))
        
        if 'dexterity' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.DEXTERITY,
                value=effects_dict['dexterity']
            ))
        
        if 'vulnerable' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.VULNERABLE,
                value=effects_dict['vulnerable'],
                target=effects_dict.get('target', 'enemy')
            ))
        
        if 'weak' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.WEAK,
                value=effects_dict['weak'],
                target=effects_dict.get('target', 'enemy')
            ))
        
        if 'poison' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.POISON,
                value=effects_dict['poison']
            ))
        
        if 'energy' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.ENERGY,
                value=effects_dict['energy']
            ))
        
        if 'double_strength' in effects_dict and effects_dict['double_strength']:
            effects.append(CardEffect(effect_type=EffectType.DOUBLE_STRENGTH))
        
        if 'hp_loss' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.HP_LOSS,
                value=effects_dict['hp_loss']
            ))
        
        if 'heal' in effects_dict:
            effects.append(CardEffect(
                effect_type=EffectType.HEAL,
                value=effects_dict['heal']
            ))
        
        if 'retain_block' in effects_dict and effects_dict['retain_block']:
            effects.append(CardEffect(effect_type=EffectType.RETAIN_BLOCK))
        
        return effects
    
    def _load_card_from_json(self, card_data: Dict, character: str) -> LoadedCard:
        """Parse a single card from JSON data."""
        keywords = []
        if card_data.get('exhaust'):
            keywords.append('exhaust')
        if card_data.get('ethereal'):
            keywords.append('ethereal')
        if card_data.get('innate'):
            keywords.append('innate')
        
        cost = card_data.get('cost', 0)
        if cost == 'X':
            cost = -1  # X-cost indicator
        
        effects = self._parse_effects(card_data.get('effects', {}))
        
        # Parse upgraded effects if present
        upgraded_effects = []
        if 'upgraded' in card_data:
            upgraded_data = card_data['upgraded']
            if 'effects' in upgraded_data:
                upgraded_effects = self._parse_effects(upgraded_data['effects'])
        
        return LoadedCard(
            name=card_data['name'],
            cost=cost,
            card_type=self._parse_card_type(card_data.get('type', 'Attack')),
            rarity=card_data.get('rarity', 'Common'),
            character=character,
            effects=effects,
            upgraded_effects=upgraded_effects,
            keywords=keywords,
            synergies=card_data.get('synergies', []),
            description=card_data.get('description', '')
        )
    
    def load_all(self) -> None:
        """Load all cards from JSON files."""
        if self._loaded:
            return
        
        card_files = [
            ('ironclad_cards.json', 'Ironclad'),
            ('silent_cards.json', 'Silent'),
            ('defect_cards.json', 'Defect'),
            ('watcher_cards.json', 'Watcher'),
        ]
        
        for filename, character in card_files:
            filepath = self.data_dir / filename
            if not filepath.exists():
                continue
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Load starter cards
            for card_data in data.get('starter_cards', []):
                card = self._load_card_from_json(card_data, character)
                self._cache[card.name.lower()] = card
            
            # Load common cards
            for card_data in data.get('common_cards', []):
                card = self._load_card_from_json(card_data, character)
                self._cache[card.name.lower()] = card
            
            # Load uncommon cards
            for card_data in data.get('uncommon_cards', []):
                card = self._load_card_from_json(card_data, character)
                self._cache[card.name.lower()] = card
            
            # Load rare cards
            for card_data in data.get('rare_cards', []):
                card = self._load_card_from_json(card_data, character)
                self._cache[card.name.lower()] = card
        
        self._loaded = True
    
    def get_card(self, name: str, upgraded: bool = False) -> Optional[Card]:
        """
        Get a card by name.
        
        Args:
            name: Card name (case-insensitive).
            upgraded: Whether to get the upgraded version.
        
        Returns:
            Card instance, or None if not found.
        """
        self.load_all()
        
        loaded = self._cache.get(name.lower())
        if loaded:
            return loaded.to_engine_card(upgraded)
        return None
    
    def get_cards_by_character(self, character: str) -> List[Card]:
        """
        Get all cards for a character.
        
        Args:
            character: Character name.
        
        Returns:
            List of Card instances.
        """
        self.load_all()
        
        return [
            card.to_engine_card()
            for card in self._cache.values()
            if card.character.lower() == character.lower()
        ]
    
    def get_cards_by_rarity(self, rarity: str) -> List[Card]:
        """
        Get all cards of a specific rarity.
        
        Args:
            rarity: Card rarity (Common, Uncommon, Rare, etc.).
        
        Returns:
            List of Card instances.
        """
        self.load_all()
        
        return [
            card.to_engine_card()
            for card in self._cache.values()
            if card.rarity.lower() == rarity.lower()
        ]
    
    def get_loaded_card(self, name: str) -> Optional[LoadedCard]:
        """
        Get the full LoadedCard data structure.
        
        Args:
            name: Card name (case-insensitive).
        
        Returns:
            LoadedCard instance, or None if not found.
        """
        self.load_all()
        return self._cache.get(name.lower())
    
    def get_all_cards(self) -> List[LoadedCard]:
        """Get all loaded cards."""
        self.load_all()
        return list(self._cache.values())


# Global card loader instance
_card_loader: Optional[CardLoader] = None


def get_card_loader() -> CardLoader:
    """Get the global card loader instance."""
    global _card_loader
    if _card_loader is None:
        _card_loader = CardLoader()
    return _card_loader


def load_card(name: str, upgraded: bool = False) -> Optional[Card]:
    """
    Convenience function to load a card by name.
    
    Args:
        name: Card name.
        upgraded: Whether to get the upgraded version.
    
    Returns:
        Card instance, or None if not found.
    """
    return get_card_loader().get_card(name, upgraded)
