"""
Provenance module for Slay the Spire simulation.
Captures and stores reproducibility metadata per critical review recommendations.

Implements:
- Git commit SHA
- Config version hash
- Environment version (Python, platform, dependencies)
- Dataset versions (card DB, enemy scripts)
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class EnvironmentInfo:
    """Environment information for reproducibility."""
    python_version: str
    platform_system: str
    platform_release: str
    platform_machine: str
    pip_freeze_sha256: str
    numpy_version: str
    pandas_version: str


@dataclass
class DatasetVersions:
    """Version information for game data files."""
    cards_sha256: Dict[str, str] = field(default_factory=dict)
    relics_sha256: str = ""
    enemies_sha256: str = ""
    keywords_sha256: str = ""


@dataclass
class ProvenanceInfo:
    """
    Complete provenance information for a simulation run.
    
    As recommended in critical review Section 3:
    - git_commit: Git commit SHA
    - config_sha256: Hash of run configuration
    - environment: Environment version info
    - dataset_versions: Hashes of data files
    """
    timestamp: str
    git_commit: str
    git_branch: str
    git_dirty: bool
    config_sha256: str
    environment: EnvironmentInfo
    dataset_versions: DatasetVersions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp,
            'git_commit': self.git_commit,
            'git_branch': self.git_branch,
            'git_dirty': self.git_dirty,
            'config_sha256': self.config_sha256,
            'environment': asdict(self.environment),
            'dataset_versions': asdict(self.dataset_versions)
        }


def get_git_commit() -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown"


def get_git_branch() -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown"


def is_git_dirty() -> bool:
    """Check if git working directory has uncommitted changes."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return len(result.stdout.strip()) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return True  # Assume dirty if we can't check


def get_pip_freeze_hash() -> str:
    """Get SHA256 hash of pip freeze output."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'freeze'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return hashlib.sha256(result.stdout.encode()).hexdigest()[:16]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown"


def get_file_hash(filepath: Path) -> str:
    """Get SHA256 hash of a file."""
    if not filepath.exists():
        return "not_found"
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except IOError:
        return "error"


def get_config_hash(config: Dict) -> str:
    """Get SHA256 hash of configuration dictionary."""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def get_environment_info() -> EnvironmentInfo:
    """Collect environment information."""
    try:
        import numpy as np
        numpy_version = np.__version__
    except ImportError:
        numpy_version = "not_installed"
    
    try:
        import pandas as pd
        pandas_version = pd.__version__
    except ImportError:
        pandas_version = "not_installed"
    
    return EnvironmentInfo(
        python_version=sys.version.split()[0],
        platform_system=platform.system(),
        platform_release=platform.release(),
        platform_machine=platform.machine(),
        pip_freeze_sha256=get_pip_freeze_hash(),
        numpy_version=numpy_version,
        pandas_version=pandas_version
    )


def get_dataset_versions(data_dir: Path = None) -> DatasetVersions:
    """
    Collect version hashes for game data files.
    
    Args:
        data_dir: Path to data directory. Defaults to ./data
    
    Returns:
        DatasetVersions with hashes of all data files.
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / 'data'
    
    versions = DatasetVersions()
    
    # Hash card files
    cards_dir = data_dir / 'cards'
    if cards_dir.exists():
        for card_file in cards_dir.glob('*.json'):
            versions.cards_sha256[card_file.stem] = get_file_hash(card_file)
    
    # Hash other data files
    versions.relics_sha256 = get_file_hash(data_dir / 'relics' / 'relics.json')
    versions.enemies_sha256 = get_file_hash(data_dir / 'enemies' / 'enemies.json')
    versions.keywords_sha256 = get_file_hash(data_dir / 'keywords' / 'keywords.json')
    
    return versions


def create_provenance(config: Dict, data_dir: Path = None) -> ProvenanceInfo:
    """
    Create complete provenance information for a simulation run.
    
    Args:
        config: Run configuration dictionary.
        data_dir: Path to data directory.
    
    Returns:
        ProvenanceInfo with all reproducibility metadata.
    """
    return ProvenanceInfo(
        timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        git_commit=get_git_commit(),
        git_branch=get_git_branch(),
        git_dirty=is_git_dirty(),
        config_sha256=get_config_hash(config),
        environment=get_environment_info(),
        dataset_versions=get_dataset_versions(data_dir)
    )


def save_provenance(provenance: ProvenanceInfo, output_path: Path) -> None:
    """
    Save provenance information to JSON file.
    
    Args:
        provenance: ProvenanceInfo to save.
        output_path: Path to output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(provenance.to_dict(), f, indent=2)


def load_provenance(input_path: Path) -> Dict[str, Any]:
    """
    Load provenance information from JSON file.
    
    Args:
        input_path: Path to input JSON file.
    
    Returns:
        Dictionary with provenance information.
    """
    with open(input_path, 'r') as f:
        return json.load(f)


def verify_provenance(
    current_provenance: ProvenanceInfo,
    expected_provenance: Dict[str, Any]
) -> Dict[str, List[str]]:
    """
    Verify current environment matches expected provenance.
    
    Args:
        current_provenance: Current environment's provenance.
        expected_provenance: Expected provenance from a previous run.
    
    Returns:
        Dictionary with 'warnings' and 'errors' lists.
    """
    issues = {'warnings': [], 'errors': []}
    current = current_provenance.to_dict()
    
    # Check git commit
    if current['git_commit'] != expected_provenance.get('git_commit'):
        issues['warnings'].append(
            f"Git commit mismatch: current={current['git_commit']}, "
            f"expected={expected_provenance.get('git_commit')}"
        )
    
    # Check if current working directory is dirty
    if current['git_dirty']:
        issues['warnings'].append("Current working directory has uncommitted changes")
    
    # Check Python version
    expected_env = expected_provenance.get('environment', {})
    if current['environment']['python_version'] != expected_env.get('python_version'):
        issues['warnings'].append(
            f"Python version mismatch: current={current['environment']['python_version']}, "
            f"expected={expected_env.get('python_version')}"
        )
    
    # Check pip freeze hash
    if current['environment']['pip_freeze_sha256'] != expected_env.get('pip_freeze_sha256'):
        issues['warnings'].append(
            f"Dependency hash mismatch: current={current['environment']['pip_freeze_sha256']}, "
            f"expected={expected_env.get('pip_freeze_sha256')}"
        )
    
    # Check dataset versions
    expected_data = expected_provenance.get('dataset_versions', {})
    current_data = current['dataset_versions']
    
    for key in ['relics_sha256', 'enemies_sha256', 'keywords_sha256']:
        if current_data.get(key) != expected_data.get(key):
            issues['warnings'].append(
                f"Data file hash mismatch for {key}: "
                f"current={current_data.get(key)}, expected={expected_data.get(key)}"
            )
    
    return issues


# Convenience function for quick provenance string
def get_provenance_string(config: Dict = None) -> str:
    """
    Get a short provenance string for logging.
    
    Args:
        config: Optional config to include in hash.
    
    Returns:
        Short string like "abc1234-3.11-linux-2024-01-15"
    """
    commit = get_git_commit()[:7]
    py_ver = sys.version.split()[0]
    plat = platform.system().lower()
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    parts = [commit, py_ver, plat, date]
    if config:
        parts.append(get_config_hash(config)[:8])
    
    return '-'.join(parts)
