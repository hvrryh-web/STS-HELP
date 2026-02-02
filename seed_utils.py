"""
Seed utilities for deterministic child RNG generation.
Uses numpy.random.SeedSequence for reproducible simulation runs.

Resolution for G1 (RNG determinism inconsistency).
"""

import hashlib
from typing import Tuple, Optional
import numpy as np


def make_child_generator(
    root_seed: int,
    archetype: str,
    relic: str,
    batch_index: int
) -> np.random.Generator:
    """
    Create a deterministic child RNG using SeedSequence.
    
    Args:
        root_seed: Root seed for the entire simulation.
        archetype: Character archetype (e.g., 'Ironclad', 'Silent').
        relic: Relic name or 'none'.
        batch_index: Batch index for parallel runs.
    
    Returns:
        A numpy random Generator with deterministic state.
    """
    # Create a unique spawn key from the parameters
    spawn_key = _create_spawn_key(archetype, relic, batch_index)
    
    # Create SeedSequence with root seed and spawn key
    seed_seq = np.random.SeedSequence(root_seed, spawn_key=(spawn_key,))
    
    return np.random.Generator(np.random.PCG64(seed_seq))


def _create_spawn_key(archetype: str, relic: str, batch_index: int) -> int:
    """
    Create a deterministic spawn key from parameters.
    
    Args:
        archetype: Character archetype.
        relic: Relic name.
        batch_index: Batch index.
    
    Returns:
        Integer spawn key derived from parameters.
    """
    key_string = f"{archetype}:{relic}:{batch_index}"
    hash_bytes = hashlib.sha256(key_string.encode()).digest()
    # Use first 8 bytes as spawn key
    return int.from_bytes(hash_bytes[:8], byteorder='little')


def generate_patch_id(
    date_str: str,
    character_code: str,
    root_seed: int,
    batch_index: Optional[int] = None,
    metadata: Optional[dict] = None
) -> str:
    """
    Generate a Patch ID for traceability.
    
    Format: PATCH-{YYYYMMDD}-{CHAR}-{SEEDHEX}-{BATCHIDX}-{HASH4}
    
    Args:
        date_str: Date string in YYYYMMDD format.
        character_code: Character code (ICL, SNT, DFT, WTR).
        root_seed: Root seed for the simulation.
        batch_index: Batch index or None for merged final.
        metadata: Optional metadata dict for hash computation.
    
    Returns:
        Patch ID string.
    """
    seed_hex = f"{root_seed:08x}"[:8]
    batch_str = str(batch_index) if batch_index is not None else "ALL"
    
    # Compute hash of metadata
    meta_str = str(metadata or {})
    hash_full = hashlib.sha1(
        f"{date_str}:{character_code}:{seed_hex}:{batch_str}:{meta_str}".encode()
    ).hexdigest()
    hash4 = hash_full[-4:]
    
    return f"PATCH-{date_str}-{character_code}-{seed_hex}-{batch_str}-{hash4}"


def get_character_code(character: str) -> str:
    """
    Get the three-letter character code.
    
    Args:
        character: Full character name.
    
    Returns:
        Three-letter code.
    """
    codes = {
        'Ironclad': 'ICL',
        'Silent': 'SNT',
        'Defect': 'DFT',
        'Watcher': 'WTR',
    }
    return codes.get(character, 'UNK')
