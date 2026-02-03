"""
Relic data model for Slay the Spire.

This module defines the Relic dataclass with metadata
including effects, synergies, and tier scoring.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class RelicRarity(Enum):
    """Relic rarity enumeration."""
    STARTER = "Starter"
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    BOSS = "Boss"
    SHOP = "Shop"
    EVENT = "Event"


@dataclass
class Relic:
    """
    Represents a Slay the Spire relic.
    
    Attributes:
        name: Relic name
        rarity: Relic rarity (Starter, Common, Uncommon, Rare, Boss, Shop, Event)
        effect: Description of the relic's effect
        synergies: List of cards/mechanics/relics that synergize
        tier_score: Numeric score for evaluation (0-100)
        character_specific: Character this relic is for (None if any)
        notes: Additional notes or commentary
    """
    name: str
    rarity: RelicRarity
    effect: str
    synergies: List[str] = field(default_factory=list)
    tier_score: float = 50.0
    character_specific: str = None
    notes: str = ""
    
    def __post_init__(self):
        """Validate relic data after initialization."""
        if not 0 <= self.tier_score <= 100:
            raise ValueError(f"Tier score must be 0-100, got {self.tier_score}")
    
    def get_value(self) -> float:
        """
        Calculate the overall value of this relic.
        
        Returns:
            Tier score as a proxy for relic value
        """
        return self.tier_score
    
    def has_synergy(self, tag: str) -> bool:
        """
        Check if relic has synergy with a given tag.
        
        Args:
            tag: Synergy tag to check
            
        Returns:
            True if relic synergizes with the tag
        """
        return tag in self.synergies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relic to dictionary representation."""
        return {
            "name": self.name,
            "rarity": self.rarity.value,
            "effect": self.effect,
            "synergies": self.synergies,
            "tier_score": self.tier_score,
            "character_specific": self.character_specific,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relic':
        """Create Relic from dictionary representation."""
        return cls(
            name=data["name"],
            rarity=RelicRarity(data["rarity"]),
            effect=data["effect"],
            synergies=data.get("synergies", []),
            tier_score=data.get("tier_score", 50.0),
            character_specific=data.get("character_specific"),
            notes=data.get("notes", ""),
        )
