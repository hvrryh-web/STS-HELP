"""
Tests for provenance module.
"""

import json
import tempfile
from pathlib import Path
import pytest

from provenance import (
    get_git_commit,
    get_git_branch,
    get_config_hash,
    get_environment_info,
    create_provenance,
    save_provenance,
    load_provenance,
    verify_provenance,
    get_provenance_string,
)


class TestProvenanceBasics:
    """Tests for basic provenance functions."""
    
    def test_get_git_commit_returns_string(self):
        """Git commit should return a string."""
        commit = get_git_commit()
        assert isinstance(commit, str)
        # Either a valid commit SHA or 'unknown'
        assert len(commit) > 0
    
    def test_get_git_branch_returns_string(self):
        """Git branch should return a string."""
        branch = get_git_branch()
        assert isinstance(branch, str)
        assert len(branch) > 0
    
    def test_get_config_hash_deterministic(self):
        """Config hash should be deterministic."""
        config = {'seed': 42, 'runs': 1000}
        hash1 = get_config_hash(config)
        hash2 = get_config_hash(config)
        assert hash1 == hash2
    
    def test_get_config_hash_different_configs(self):
        """Different configs should produce different hashes."""
        config1 = {'seed': 42}
        config2 = {'seed': 43}
        hash1 = get_config_hash(config1)
        hash2 = get_config_hash(config2)
        assert hash1 != hash2
    
    def test_get_environment_info(self):
        """Environment info should contain required fields."""
        env = get_environment_info()
        assert hasattr(env, 'python_version')
        assert hasattr(env, 'platform_system')
        assert hasattr(env, 'numpy_version')
        assert hasattr(env, 'pandas_version')


class TestProvenanceCreation:
    """Tests for provenance creation and serialization."""
    
    def test_create_provenance(self):
        """Provenance should be created with all fields."""
        config = {'seed': 42, 'runs': 100}
        prov = create_provenance(config)
        
        assert prov.timestamp is not None
        assert prov.git_commit is not None
        assert prov.config_sha256 is not None
        assert prov.environment is not None
        assert prov.dataset_versions is not None
    
    def test_provenance_to_dict(self):
        """Provenance should convert to dictionary."""
        config = {'seed': 42}
        prov = create_provenance(config)
        prov_dict = prov.to_dict()
        
        assert isinstance(prov_dict, dict)
        assert 'timestamp' in prov_dict
        assert 'git_commit' in prov_dict
        assert 'environment' in prov_dict
    
    def test_save_and_load_provenance(self):
        """Provenance should save and load correctly."""
        config = {'seed': 42}
        prov = create_provenance(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'provenance.json'
            save_provenance(prov, path)
            
            loaded = load_provenance(path)
            assert loaded['git_commit'] == prov.git_commit
            assert loaded['config_sha256'] == prov.config_sha256


class TestProvenanceVerification:
    """Tests for provenance verification."""
    
    def test_verify_matching_provenance(self):
        """Matching provenance should have no errors."""
        config = {'seed': 42}
        prov1 = create_provenance(config)
        expected = prov1.to_dict()
        
        issues = verify_provenance(prov1, expected)
        
        # Should have no errors (warnings possible if git is dirty)
        assert 'errors' in issues
        assert len(issues['errors']) == 0
    
    def test_verify_different_commit(self):
        """Different commit should produce warning."""
        config = {'seed': 42}
        prov = create_provenance(config)
        expected = prov.to_dict()
        expected['git_commit'] = 'different_commit_sha'
        
        issues = verify_provenance(prov, expected)
        
        # Should have a warning about commit mismatch
        assert any('commit' in w.lower() for w in issues['warnings'])


class TestProvenanceString:
    """Tests for provenance string generation."""
    
    def test_get_provenance_string_format(self):
        """Provenance string should have expected format."""
        prov_str = get_provenance_string()
        
        # Should contain date-like pattern
        assert '-' in prov_str
        parts = prov_str.split('-')
        assert len(parts) >= 4
    
    def test_get_provenance_string_with_config(self):
        """Provenance string with config should include hash."""
        config = {'seed': 42}
        prov_str = get_provenance_string(config)
        
        # Should have additional hash component
        parts = prov_str.split('-')
        assert len(parts) >= 5
