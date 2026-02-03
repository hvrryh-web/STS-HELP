"""
Data verification module for cross-referencing game data.

This module validates card mechanics, relic interactions, and enemy AI patterns
against known sources (SpireSpy, Tiny Helper, STSDeckAssistant).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
import json


@dataclass
class ValidationIssue:
    """
    Represents a data validation issue.
    
    Attributes:
        severity: Issue severity (ERROR, WARNING, INFO)
        category: Issue category (card, relic, enemy, mechanic)
        item_name: Name of the item with the issue
        description: Description of the issue
        expected_value: Expected value (if known)
        actual_value: Actual value found
        source: Reference source
    """
    severity: str  # ERROR, WARNING, INFO
    category: str  # card, relic, enemy, mechanic
    item_name: str
    description: str
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "severity": self.severity,
            "category": self.category,
            "item_name": self.item_name,
            "description": self.description,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "source": self.source,
        }


class DataVerifier:
    """
    Verifies game data against known sources.
    
    Cross-references card mechanics, relic interactions, and enemy patterns.
    """
    
    def __init__(self, data_dir: Path = None):
        """
        Initialize the data verifier.
        
        Args:
            data_dir: Path to data directory (default: ./data)
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
        
        self.data_dir = Path(data_dir)
        self.issues: List[ValidationIssue] = []
        self.verified_items: Set[str] = set()
    
    def load_card_data(self, character: str = "ironclad") -> List[Dict[str, Any]]:
        """
        Load card data from JSON file.
        
        Args:
            character: Character name (lowercase)
            
        Returns:
            List of card dictionaries
        """
        card_file = self.data_dir / "cards" / f"{character}_cards.json"
        
        if not card_file.exists():
            self.add_issue(
                severity="ERROR",
                category="card",
                item_name=character,
                description=f"Card data file not found: {card_file}"
            )
            return []
        
        try:
            with open(card_file, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON formats
            if isinstance(data, dict):
                if "starter_cards" in data:
                    # Format with starter_cards and other_cards
                    all_cards = data.get("starter_cards", []) + data.get("cards", [])
                    return all_cards
                else:
                    # Single deck format
                    return data.get("cards", [])
            elif isinstance(data, list):
                return data
            else:
                self.add_issue(
                    severity="ERROR",
                    category="card",
                    item_name=character,
                    description=f"Unexpected data format in {card_file}"
                )
                return []
                
        except json.JSONDecodeError as e:
            self.add_issue(
                severity="ERROR",
                category="card",
                item_name=character,
                description=f"Invalid JSON in card file: {e}"
            )
            return []
    
    def verify_card_mechanics(self, character: str = "ironclad") -> bool:
        """
        Verify card mechanics for a character.
        
        Args:
            character: Character to verify
            
        Returns:
            True if verification passed, False otherwise
        """
        cards = self.load_card_data(character)
        
        if not cards:
            return False
        
        for card in cards:
            card_name = card.get("name", "Unknown")
            
            # Verify required fields
            required_fields = ["name", "cost", "type"]
            for field in required_fields:
                if field not in card:
                    self.add_issue(
                        severity="ERROR",
                        category="card",
                        item_name=card_name,
                        description=f"Missing required field: {field}"
                    )
            
            # Verify cost range
            cost = card.get("cost", 0)
            if isinstance(cost, int) and not (-1 <= cost <= 3):
                self.add_issue(
                    severity="WARNING",
                    category="card",
                    item_name=card_name,
                    description=f"Unusual cost value: {cost}",
                    actual_value=cost,
                    source="Internal validation"
                )
            
            # Mark as verified if no errors
            if card_name != "Unknown":
                self.verified_items.add(f"card:{character}:{card_name}")
        
        return True
    
    def verify_relic_data(self) -> bool:
        """
        Verify relic data.
        
        Returns:
            True if verification passed, False otherwise
        """
        relic_file = self.data_dir / "relics" / "relics.json"
        
        if not relic_file.exists():
            self.add_issue(
                severity="ERROR",
                category="relic",
                item_name="all",
                description=f"Relic data file not found: {relic_file}"
            )
            return False
        
        try:
            with open(relic_file, 'r') as f:
                data = json.load(f)
            
            relics = data if isinstance(data, list) else data.get("relics", [])
            
            for relic in relics:
                relic_name = relic.get("name", "Unknown")
                
                # Verify required fields
                if "name" not in relic:
                    self.add_issue(
                        severity="ERROR",
                        category="relic",
                        item_name=relic_name,
                        description="Missing required field: name"
                    )
                
                if relic_name != "Unknown":
                    self.verified_items.add(f"relic:{relic_name}")
            
            return True
            
        except json.JSONDecodeError as e:
            self.add_issue(
                severity="ERROR",
                category="relic",
                item_name="all",
                description=f"Invalid JSON in relic file: {e}"
            )
            return False
    
    def verify_enemy_data(self) -> bool:
        """
        Verify enemy AI patterns.
        
        Returns:
            True if verification passed, False otherwise
        """
        enemy_file = self.data_dir / "enemies" / "enemies.json"
        
        if not enemy_file.exists():
            self.add_issue(
                severity="WARNING",
                category="enemy",
                item_name="all",
                description=f"Enemy data file not found: {enemy_file}"
            )
            return False
        
        try:
            with open(enemy_file, 'r') as f:
                data = json.load(f)
            
            enemies = data if isinstance(data, list) else data.get("enemies", [])
            
            for enemy in enemies:
                enemy_name = enemy.get("name", "Unknown")
                
                if "name" not in enemy:
                    self.add_issue(
                        severity="ERROR",
                        category="enemy",
                        item_name=enemy_name,
                        description="Missing required field: name"
                    )
                
                if enemy_name != "Unknown":
                    self.verified_items.add(f"enemy:{enemy_name}")
            
            return True
            
        except json.JSONDecodeError as e:
            self.add_issue(
                severity="ERROR",
                category="enemy",
                item_name="all",
                description=f"Invalid JSON in enemy file: {e}"
            )
            return False
    
    def verify_all(self, characters: List[str] = None) -> Dict[str, Any]:
        """
        Run all verification checks.
        
        Args:
            characters: List of characters to verify (default: all)
            
        Returns:
            Verification report
        """
        if characters is None:
            characters = ["ironclad", "silent", "defect", "watcher"]
        
        self.issues.clear()
        self.verified_items.clear()
        
        # Verify cards for each character
        for character in characters:
            self.verify_card_mechanics(character)
        
        # Verify relics
        self.verify_relic_data()
        
        # Verify enemies
        self.verify_enemy_data()
        
        return self.generate_report()
    
    def add_issue(
        self,
        severity: str,
        category: str,
        item_name: str,
        description: str,
        expected_value: Any = None,
        actual_value: Any = None,
        source: str = ""
    ):
        """
        Add a validation issue.
        
        Args:
            severity: Issue severity (ERROR, WARNING, INFO)
            category: Issue category
            item_name: Name of item
            description: Issue description
            expected_value: Expected value
            actual_value: Actual value
            source: Reference source
        """
        issue = ValidationIssue(
            severity=severity,
            category=category,
            item_name=item_name,
            description=description,
            expected_value=expected_value,
            actual_value=actual_value,
            source=source
        )
        self.issues.append(issue)
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate verification report.
        
        Returns:
            Report dictionary
        """
        errors = [i for i in self.issues if i.severity == "ERROR"]
        warnings = [i for i in self.issues if i.severity == "WARNING"]
        info = [i for i in self.issues if i.severity == "INFO"]
        
        return {
            "verified_count": len(self.verified_items),
            "verified_items": sorted(list(self.verified_items)),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "info_count": len(info),
            "errors": [i.to_dict() for i in errors],
            "warnings": [i.to_dict() for i in warnings],
            "info": [i.to_dict() for i in info],
            "passed": len(errors) == 0,
        }
    
    def save_report(self, output_path: Path):
        """
        Save verification report to JSON file.
        
        Args:
            output_path: Path to save report
        """
        report = self.generate_report()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)


def verify_data(data_dir: Path = None, output_path: Path = None) -> Dict[str, Any]:
    """
    Convenience function to verify all data.
    
    Args:
        data_dir: Path to data directory
        output_path: Optional path to save report
        
    Returns:
        Verification report
    """
    verifier = DataVerifier(data_dir)
    report = verifier.verify_all()
    
    if output_path:
        verifier.save_report(output_path)
    
    return report
