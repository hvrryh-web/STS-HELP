"""
Unit tests for src.verification module.
"""

import pytest
from pathlib import Path
import tempfile
import json

from src.verification.verifier import DataVerifier, ValidationIssue, verify_data


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""
    
    def test_issue_creation(self):
        """ValidationIssue can be created."""
        issue = ValidationIssue(
            severity="ERROR",
            category="card",
            item_name="Strike",
            description="Missing field"
        )
        
        assert issue.severity == "ERROR"
        assert issue.category == "card"
        assert issue.item_name == "Strike"
    
    def test_issue_to_dict(self):
        """ValidationIssue can be converted to dict."""
        issue = ValidationIssue(
            severity="WARNING",
            category="relic",
            item_name="Dead Branch",
            description="High tier score"
        )
        
        issue_dict = issue.to_dict()
        
        assert issue_dict["severity"] == "WARNING"
        assert issue_dict["category"] == "relic"


class TestDataVerifier:
    """Tests for DataVerifier class."""
    
    def test_verifier_initialization(self):
        """DataVerifier can be initialized."""
        verifier = DataVerifier()
        
        assert verifier.data_dir.exists()
        assert len(verifier.issues) == 0
        assert len(verifier.verified_items) == 0
    
    def test_verifier_custom_data_dir(self):
        """DataVerifier can use custom data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = DataVerifier(data_dir=Path(tmpdir))
            
            assert verifier.data_dir == Path(tmpdir)
    
    def test_load_card_data(self):
        """Card data can be loaded from JSON."""
        verifier = DataVerifier()
        cards = verifier.load_card_data("ironclad")
        
        # Should load existing ironclad cards
        assert isinstance(cards, list)
        # May be empty or populated depending on file existence
    
    def test_load_card_data_nonexistent(self):
        """Loading nonexistent card data adds error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = DataVerifier(data_dir=Path(tmpdir))
            cards = verifier.load_card_data("nonexistent")
            
            assert len(cards) == 0
            assert len(verifier.issues) > 0
            assert any(i.severity == "ERROR" for i in verifier.issues)
    
    def test_verify_card_mechanics(self):
        """Card mechanics can be verified."""
        verifier = DataVerifier()
        
        # This will verify actual card data if it exists
        result = verifier.verify_card_mechanics("ironclad")
        
        # Should return boolean
        assert isinstance(result, bool)
    
    def test_verify_card_with_test_data(self):
        """Card verification works with test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            cards_dir = tmpdir / "cards"
            cards_dir.mkdir()
            
            # Create test card data
            test_cards = [
                {
                    "name": "Strike",
                    "cost": 1,
                    "type": "Attack"
                },
                {
                    "name": "Defend",
                    "cost": 1,
                    "type": "Skill"
                }
            ]
            
            with open(cards_dir / "ironclad_cards.json", 'w') as f:
                json.dump(test_cards, f)
            
            verifier = DataVerifier(data_dir=tmpdir)
            result = verifier.verify_card_mechanics("ironclad")
            
            assert result is True
            assert len(verifier.verified_items) == 2
    
    def test_verify_relic_data(self):
        """Relic data can be verified."""
        verifier = DataVerifier()
        
        # This will verify actual relic data if it exists
        result = verifier.verify_relic_data()
        
        # Should return boolean
        assert isinstance(result, bool)
    
    def test_verify_enemy_data(self):
        """Enemy data can be verified."""
        verifier = DataVerifier()
        
        # This will verify actual enemy data if it exists
        result = verifier.verify_enemy_data()
        
        # Should return boolean
        assert isinstance(result, bool)
    
    def test_add_issue(self):
        """Issues can be added to verifier."""
        verifier = DataVerifier()
        
        verifier.add_issue(
            severity="WARNING",
            category="card",
            item_name="Test",
            description="Test issue"
        )
        
        assert len(verifier.issues) == 1
        assert verifier.issues[0].severity == "WARNING"
    
    def test_generate_report(self):
        """Report can be generated."""
        verifier = DataVerifier()
        
        verifier.add_issue("ERROR", "card", "Test1", "Error test")
        verifier.add_issue("WARNING", "relic", "Test2", "Warning test")
        verifier.verified_items.add("card:test:item")
        
        report = verifier.generate_report()
        
        assert "error_count" in report
        assert "warning_count" in report
        assert "verified_count" in report
        assert "passed" in report
        assert report["error_count"] == 1
        assert report["warning_count"] == 1
        assert report["verified_count"] == 1
        assert report["passed"] is False  # Has errors
    
    def test_generate_report_no_errors(self):
        """Report passes when no errors."""
        verifier = DataVerifier()
        
        verifier.add_issue("WARNING", "card", "Test", "Warning only")
        verifier.verified_items.add("card:test:item")
        
        report = verifier.generate_report()
        
        assert report["passed"] is True  # Only warnings, no errors
    
    def test_verify_all(self):
        """All verifications can be run."""
        verifier = DataVerifier()
        
        report = verifier.verify_all(characters=["ironclad"])
        
        assert isinstance(report, dict)
        assert "verified_count" in report
        assert "error_count" in report
        assert "passed" in report
    
    def test_save_report(self):
        """Report can be saved to file."""
        verifier = DataVerifier()
        verifier.add_issue("ERROR", "card", "Test", "Test issue")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            verifier.save_report(output_path)
            
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "error_count" in data
            assert data["error_count"] == 1


class TestVerifyData:
    """Tests for verify_data convenience function."""
    
    def test_verify_data_returns_report(self):
        """verify_data returns report dictionary."""
        report = verify_data()
        
        assert isinstance(report, dict)
        assert "verified_count" in report
        assert "error_count" in report
    
    def test_verify_data_saves_report(self):
        """verify_data can save report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "verification.json"
            
            report = verify_data(output_path=output_path)
            
            assert output_path.exists()
