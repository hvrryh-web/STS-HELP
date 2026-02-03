"""
Card data model for Slay the Spire.

This module defines the Card dataclass with comprehensive metadata
including tier grades, tags, and synergy information.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class CardType(Enum):
    """Card type enumeration."""
    ATTACK = "Attack"
    SKILL = "Skill"
    POWER = "Power"
    STATUS = "Status"
    CURSE = "Curse"


class Rarity(Enum):
    """Card rarity enumeration."""
    BASIC = "Basic"
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    SPECIAL = "Special"
    CURSE = "Curse"


@dataclass
class Card:
    """
    Represents a Slay the Spire card with comprehensive metadata.
    
    Attributes:
        name: Card name
        card_type: Type of card (Attack, Skill, Power, etc.)
        cost: Energy cost to play the card
        rarity: Card rarity (Basic, Common, Uncommon, Rare)
        tier_grade: Letter grade for tier list (S, A, B, C, D, F)
        tier_score: Numeric score for evaluation (0-100)
        form_tags: Tags describing card form (e.g., "AoE", "Single-target")
        function_tags: Tags describing function (e.g., "Damage", "Block")
        fusion_tags: Tags for synergy potential (e.g., "Strength-scaling")
        synergies: List of cards/mechanics that synergize
        notes: Additional notes or commentary
        effects: Dictionary of card effects
        upgraded_effects: Effects when upgraded (optional)
    """
    name: str
    card_type: CardType
    cost: int
    rarity: Rarity
    tier_grade: str = "C"
    tier_score: float = 50.0
    form_tags: List[str] = field(default_factory=list)
    function_tags: List[str] = field(default_factory=list)
    fusion_tags: List[str] = field(default_factory=list)
    synergies: List[str] = field(default_factory=list)
    notes: str = ""
    effects: Dict[str, Any] = field(default_factory=dict)
    upgraded_effects: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate card data after initialization."""
        if self.cost < 0 and self.cost != -1:  # -1 is X-cost
            raise ValueError(f"Invalid cost: {self.cost}")
        if not 0 <= self.tier_score <= 100:
            raise ValueError(f"Tier score must be 0-100, got {self.tier_score}")
        if self.tier_grade not in ["S", "A", "B", "C", "D", "F"]:
            raise ValueError(f"Invalid tier grade: {self.tier_grade}")
    
    def get_value(self) -> float:
        """
        Calculate the overall value of this card.
        
        Returns:
            Tier score as a proxy for card value
        """
        return self.tier_score
    
    def has_synergy(self, tag: str) -> bool:
        """
        Check if card has synergy with a given tag.
        
        Args:
            tag: Synergy tag to check
            
        Returns:
            True if card synergizes with the tag
        """
        return tag in self.synergies or tag in self.fusion_tags
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert card to dictionary representation."""
        return {
            "name": self.name,
            "card_type": self.card_type.value,
            "cost": self.cost,
            "rarity": self.rarity.value,
            "tier_grade": self.tier_grade,
            "tier_score": self.tier_score,
            "form_tags": self.form_tags,
            "function_tags": self.function_tags,
            "fusion_tags": self.fusion_tags,
            "synergies": self.synergies,
            "notes": self.notes,
            "effects": self.effects,
            "upgraded_effects": self.upgraded_effects,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Card':
        """Create Card from dictionary representation."""
        return cls(
            name=data["name"],
            card_type=CardType(data["card_type"]),
            cost=data["cost"],
            rarity=Rarity(data["rarity"]),
            tier_grade=data.get("tier_grade", "C"),
            tier_score=data.get("tier_score", 50.0),
            form_tags=data.get("form_tags", []),
            function_tags=data.get("function_tags", []),
            fusion_tags=data.get("fusion_tags", []),
            synergies=data.get("synergies", []),
            notes=data.get("notes", ""),
            effects=data.get("effects", {}),
            upgraded_effects=data.get("upgraded_effects"),
        )
