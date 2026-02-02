"""
Unit tests for seed utilities.
Resolution for R1: Verification of deterministic child RNG generation.
"""

import pytest
import numpy as np

from seed_utils import make_child_generator, generate_patch_id, get_character_code


class TestMakeChildGenerator:
    """Tests for make_child_generator function."""
    
    def test_deterministic_same_inputs(self):
        """Same inputs produce identical sequences."""
        rng1 = make_child_generator(42, 'Ironclad', 'none', 0)
        rng2 = make_child_generator(42, 'Ironclad', 'none', 0)
        
        # Draw some random values
        values1 = [rng1.random() for _ in range(10)]
        values2 = [rng2.random() for _ in range(10)]
        
        assert values1 == values2
    
    def test_different_batch_index(self):
        """Different batch indices produce different sequences."""
        rng1 = make_child_generator(42, 'Ironclad', 'none', 0)
        rng2 = make_child_generator(42, 'Ironclad', 'none', 1)
        
        values1 = [rng1.random() for _ in range(10)]
        values2 = [rng2.random() for _ in range(10)]
        
        assert values1 != values2
    
    def test_different_character(self):
        """Different characters produce different sequences."""
        rng1 = make_child_generator(42, 'Ironclad', 'none', 0)
        rng2 = make_child_generator(42, 'Silent', 'none', 0)
        
        values1 = [rng1.random() for _ in range(10)]
        values2 = [rng2.random() for _ in range(10)]
        
        assert values1 != values2
    
    def test_different_relic(self):
        """Different relics produce different sequences."""
        rng1 = make_child_generator(42, 'Ironclad', 'none', 0)
        rng2 = make_child_generator(42, 'Ironclad', 'burning_blood', 0)
        
        values1 = [rng1.random() for _ in range(10)]
        values2 = [rng2.random() for _ in range(10)]
        
        assert values1 != values2
    
    def test_different_seed(self):
        """Different root seeds produce different sequences."""
        rng1 = make_child_generator(42, 'Ironclad', 'none', 0)
        rng2 = make_child_generator(43, 'Ironclad', 'none', 0)
        
        values1 = [rng1.random() for _ in range(10)]
        values2 = [rng2.random() for _ in range(10)]
        
        assert values1 != values2
    
    def test_returns_generator(self):
        """Function returns a numpy Generator."""
        rng = make_child_generator(42, 'Ironclad', 'none', 0)
        assert isinstance(rng, np.random.Generator)


class TestGeneratePatchId:
    """Tests for generate_patch_id function."""
    
    def test_patch_id_format(self):
        """Patch ID has correct format."""
        patch_id = generate_patch_id('20260101', 'ICL', 42, 0)
        
        parts = patch_id.split('-')
        assert len(parts) == 6
        assert parts[0] == 'PATCH'
        assert parts[1] == '20260101'
        assert parts[2] == 'ICL'
        assert len(parts[4]) <= 10  # Batch index
        assert len(parts[5]) == 4  # Hash
    
    def test_deterministic(self):
        """Same inputs produce same patch ID."""
        id1 = generate_patch_id('20260101', 'ICL', 42, 0)
        id2 = generate_patch_id('20260101', 'ICL', 42, 0)
        
        assert id1 == id2
    
    def test_different_inputs_different_id(self):
        """Different inputs produce different patch IDs."""
        id1 = generate_patch_id('20260101', 'ICL', 42, 0)
        id2 = generate_patch_id('20260101', 'ICL', 42, 1)
        
        assert id1 != id2
    
    def test_all_batch_format(self):
        """Batch index None produces 'ALL' in patch ID."""
        patch_id = generate_patch_id('20260101', 'ICL', 42, None)
        
        assert 'ALL' in patch_id


class TestGetCharacterCode:
    """Tests for get_character_code function."""
    
    def test_ironclad(self):
        assert get_character_code('Ironclad') == 'ICL'
    
    def test_silent(self):
        assert get_character_code('Silent') == 'SNT'
    
    def test_defect(self):
        assert get_character_code('Defect') == 'DFT'
    
    def test_watcher(self):
        assert get_character_code('Watcher') == 'WTR'
    
    def test_unknown(self):
        assert get_character_code('Unknown') == 'UNK'
