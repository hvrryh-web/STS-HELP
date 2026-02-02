"""
Unified orchestrator for Slay the Spire simulation.
Implements parallel batch runner, manifest resume, and per-batch Parquet writer.

Resolution for G6: Per-batch Parquet files with atomic merge.
"""

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import hashlib

import numpy as np
import pandas as pd

from seed_utils import make_child_generator, generate_patch_id, get_character_code


# Character engine imports
def get_engine(character: str):
    """Dynamically import and return the appropriate engine."""
    if character == 'Ironclad':
        from ironclad_engine import simulate_run
        return simulate_run
    elif character == 'Silent':
        from silent_engine import simulate_run
        return simulate_run
    elif character == 'Defect':
        from defect_engine import simulate_run
        return simulate_run
    elif character == 'Watcher':
        from watcher_engine import simulate_run
        return simulate_run
    else:
        raise ValueError(f"Unknown character: {character}")


def run_batch(
    character: str,
    relic: str,
    root_seed: int,
    batch_index: int,
    batch_size: int,
    enemy_hp: int = 120,
    max_turns: int = 50
) -> List[Dict]:
    """
    Run a batch of simulations.
    
    Args:
        character: Character name.
        relic: Relic name.
        root_seed: Root seed.
        batch_index: Batch index.
        batch_size: Number of runs in batch.
        enemy_hp: Enemy HP.
        max_turns: Maximum turns.
    
    Returns:
        List of result dictionaries.
    """
    simulate_run = get_engine(character)
    results = []
    
    for i in range(batch_size):
        # Create deterministic RNG for this run
        rng = make_child_generator(root_seed, character, relic, batch_index * batch_size + i)
        
        result = simulate_run(rng, relic=relic, enemy_hp=enemy_hp, max_turns=max_turns)
        
        result_dict = asdict(result)
        result_dict['character'] = character
        result_dict['relic'] = relic
        result_dict['root_seed'] = root_seed
        result_dict['batch_index'] = batch_index
        result_dict['run_index'] = batch_index * batch_size + i
        
        results.append(result_dict)
    
    return results


def write_batch_parquet(
    results: List[Dict],
    output_dir: Path,
    character: str,
    batch_index: int,
    patch_id: str
) -> Path:
    """
    Write batch results to Parquet file.
    
    Args:
        results: List of result dictionaries.
        output_dir: Output directory.
        character: Character name.
        batch_index: Batch index.
        patch_id: Patch ID.
    
    Returns:
        Path to written file.
    """
    df = pd.DataFrame(results)
    
    # Create output path
    batch_dir = output_dir / character
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"batch_{batch_index:04d}_{patch_id}.parquet"
    filepath = batch_dir / filename
    
    df.to_parquet(filepath, index=False)
    
    return filepath


def merge_parquet_files(
    output_dir: Path,
    character: str,
    patch_id: str
) -> Path:
    """
    Merge all batch Parquet files into a single final file.
    
    Resolution for G6: Canonical merge with atomic replace.
    
    Args:
        output_dir: Output directory.
        character: Character name.
        patch_id: Patch ID.
    
    Returns:
        Path to merged file.
    """
    batch_dir = output_dir / character
    parquet_files = sorted(batch_dir.glob("batch_*.parquet"))
    
    if not parquet_files:
        raise ValueError(f"No parquet files found in {batch_dir}")
    
    # Read and concatenate all batch files
    dfs = [pd.read_parquet(f) for f in parquet_files]
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # Write to final directory
    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    
    final_path = final_dir / f"{character}_{patch_id}.parquet"
    
    # Atomic write: write to temp then rename
    temp_path = final_dir / f"{character}_{patch_id}.tmp.parquet"
    merged_df.to_parquet(temp_path, index=False)
    temp_path.rename(final_path)
    
    return final_path


class Manifest:
    """Manifest for tracking simulation progress and resume."""
    
    def __init__(self, path: Path):
        self.path = path
        self.data: Dict[str, Any] = {
            'completed_batches': [],
            'parameters': {},
            'start_time': None,
            'last_update': None
        }
        self.load()
    
    def load(self) -> None:
        """Load manifest from disk if exists."""
        if self.path.exists():
            with open(self.path, 'r') as f:
                self.data = json.load(f)
    
    def save(self) -> None:
        """Save manifest to disk."""
        self.data['last_update'] = datetime.now().isoformat()
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def is_batch_completed(self, character: str, batch_index: int) -> bool:
        """Check if a batch is already completed."""
        key = f"{character}:{batch_index}"
        return key in self.data['completed_batches']
    
    def mark_batch_completed(self, character: str, batch_index: int) -> None:
        """Mark a batch as completed."""
        key = f"{character}:{batch_index}"
        if key not in self.data['completed_batches']:
            self.data['completed_batches'].append(key)
        self.save()
    
    def set_parameters(self, params: Dict) -> None:
        """Set simulation parameters."""
        self.data['parameters'] = params
        self.data['start_time'] = datetime.now().isoformat()
        self.save()


def run_orchestrator(
    seed: int,
    runs: int,
    batch_size: int,
    workers: int,
    characters: List[str],
    relics: List[str] = None,
    output_dir: str = "unified_outputs",
    enemy_hp: int = 120,
    max_turns: int = 50
) -> Dict[str, Any]:
    """
    Run the unified orchestrator.
    
    Args:
        seed: Root seed.
        runs: Total runs per character/relic.
        batch_size: Runs per batch.
        workers: Number of parallel workers.
        characters: List of characters to simulate.
        relics: List of relics (defaults to ['none']).
        output_dir: Output directory.
        enemy_hp: Enemy HP.
        max_turns: Maximum turns.
    
    Returns:
        Dictionary with results summary and patch IDs.
    """
    if relics is None:
        relics = ['none']
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate date string
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Initialize manifest
    manifest = Manifest(output_path / "manifest.json")
    manifest.set_parameters({
        'seed': seed,
        'runs': runs,
        'batch_size': batch_size,
        'characters': characters,
        'relics': relics,
        'enemy_hp': enemy_hp,
        'max_turns': max_turns
    })
    
    # Calculate batches
    num_batches = (runs + batch_size - 1) // batch_size
    
    results_summary = {}
    patch_ids = {}
    
    for character in characters:
        char_code = get_character_code(character)
        patch_id = generate_patch_id(date_str, char_code, seed, None, {
            'runs': runs,
            'batch_size': batch_size
        })
        patch_ids[character] = patch_id
        
        print(f"\n{'='*60}")
        print(f"Running {character} simulation")
        print(f"Patch ID: {patch_id}")
        print(f"{'='*60}")
        
        for relic in relics:
            # Collect all batch tasks
            pending_batches = []
            for batch_idx in range(num_batches):
                if not manifest.is_batch_completed(character, batch_idx):
                    pending_batches.append(batch_idx)
            
            if not pending_batches:
                print(f"All batches completed for {character}/{relic}")
                continue
            
            print(f"Running {len(pending_batches)} batches for {character}/{relic}")
            
            # Run batches in parallel
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = {}
                for batch_idx in pending_batches:
                    actual_batch_size = min(batch_size, runs - batch_idx * batch_size)
                    future = executor.submit(
                        run_batch,
                        character,
                        relic,
                        seed,
                        batch_idx,
                        actual_batch_size,
                        enemy_hp,
                        max_turns
                    )
                    futures[future] = batch_idx
                
                completed = 0
                for future in as_completed(futures):
                    batch_idx = futures[future]
                    try:
                        results = future.result()
                        
                        # Write batch to parquet
                        write_batch_parquet(
                            results,
                            output_path,
                            character,
                            batch_idx,
                            patch_id
                        )
                        
                        manifest.mark_batch_completed(character, batch_idx)
                        completed += 1
                        
                        if completed % 10 == 0 or completed == len(pending_batches):
                            print(f"  Completed {completed}/{len(pending_batches)} batches")
                    
                    except Exception as e:
                        print(f"  Error in batch {batch_idx}: {e}")
            
            # Merge parquet files
            print(f"Merging parquet files for {character}...")
            try:
                final_path = merge_parquet_files(output_path, character, patch_id)
                print(f"  Final file: {final_path}")
                
                # Compute summary statistics
                df = pd.read_parquet(final_path)
                summary = {
                    'runs': len(df),
                    'wins': df['win'].sum(),
                    'win_rate': df['win'].mean(),
                    'mean_turns': df['turns'].mean(),
                    'mean_damage': df['damage_taken'].mean(),
                    'median_damage': df['damage_taken'].median(),
                    'std_damage': df['damage_taken'].std(),
                    'mean_final_hp': df[df['win']]['final_hp'].mean() if df['win'].any() else 0,
                    'patch_id': patch_id
                }
                results_summary[f"{character}/{relic}"] = summary
                
                print(f"  Win rate: {summary['win_rate']:.2%}")
                print(f"  Mean turns: {summary['mean_turns']:.1f}")
                print(f"  Mean damage taken: {summary['mean_damage']:.1f}")
                
            except Exception as e:
                print(f"  Error merging: {e}")
    
    return {
        'summary': results_summary,
        'patch_ids': patch_ids,
        'output_dir': str(output_path)
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Slay the Spire Unified Orchestrator')
    parser.add_argument('--seed', type=int, default=42, help='Root seed')
    parser.add_argument('--runs', type=int, default=1000, help='Total runs per character')
    parser.add_argument('--batch-size', type=int, default=100, help='Runs per batch')
    parser.add_argument('--workers', type=int, default=4, help='Parallel workers')
    parser.add_argument('--characters', nargs='+', default=['Ironclad'],
                        choices=['Ironclad', 'Silent', 'Defect', 'Watcher'],
                        help='Characters to simulate')
    parser.add_argument('--relics', nargs='+', default=['none'],
                        help='Relics to test')
    parser.add_argument('--output-dir', type=str, default='unified_outputs',
                        help='Output directory')
    parser.add_argument('--enemy-hp', type=int, default=120,
                        help='Enemy HP')
    parser.add_argument('--max-turns', type=int, default=50,
                        help='Maximum turns')
    
    args = parser.parse_args()
    
    results = run_orchestrator(
        seed=args.seed,
        runs=args.runs,
        batch_size=args.batch_size,
        workers=args.workers,
        characters=args.characters,
        relics=args.relics,
        output_dir=args.output_dir,
        enemy_hp=args.enemy_hp,
        max_turns=args.max_turns
    )
    
    print("\n" + "="*60)
    print("SIMULATION COMPLETE")
    print("="*60)
    
    for key, summary in results['summary'].items():
        print(f"\n{key}:")
        print(f"  Patch ID: {summary['patch_id']}")
        print(f"  Win Rate: {summary['win_rate']:.2%}")
        print(f"  Mean Turns: {summary['mean_turns']:.1f}")
        print(f"  Mean Damage: {summary['mean_damage']:.1f}")
    
    return results


if __name__ == '__main__':
    main()
