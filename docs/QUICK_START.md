# Slay the Spire Simulation - Quick Start Guide

## Overview

This repository provides a deterministic simulation environment for **Slay the Spire**, a roguelike deck-building video game. The simulation framework supports all four playable characters and enables reproducible combat simulations for analysis, optimization, and AI training.

## Prerequisites

- Python 3.9+
- pip package manager

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/STS-HELP.git
cd STS-HELP

# Install dependencies
pip install -r requirements.txt
```

## Quick Start Commands

### 1. Run Unit Tests

Verify the installation:

```bash
pytest tests/ -v
```

### 2. Run a Basic Simulation

Run 100 Ironclad combat simulations:

```bash
python orchestrator_unified.py --seed 42 --runs 100 --batch-size 50 --workers 2 --characters Ironclad
```

### 3. Run Calibration

Calibrate all characters:

```bash
python validation_harness.py --characters Ironclad Silent Defect Watcher --runs 500
```

### 4. Generate Reports

After running a simulation:

```bash
# Generate Excel report
python -c "import reporting; reporting.generate_excel('unified_outputs', 'YOUR-PATCH-ID')"

# Generate PDF report
python -c "import reporting; reporting.generate_pdf('unified_outputs', 'YOUR-PATCH-ID')"
```

## Character Overview

| Character | Starting HP | Energy | Playstyle |
|-----------|-------------|--------|-----------|
| **Ironclad** | 80 | 3 | Strength scaling, self-damage, healing |
| **Silent** | 70 | 3 | Poison, discard synergies, shivs |
| **Defect** | 75 | 3 | Orbs (Lightning, Frost, Dark, Plasma), Focus |
| **Watcher** | 72 | 3 | Stances (Wrath, Calm, Divinity), Mantra |

## Key Concepts

### Deterministic RNG

All simulations use `numpy.random.SeedSequence` for reproducibility. The same seed always produces the same result:

```python
from seed_utils import make_child_generator

rng = make_child_generator(root_seed=42, archetype='Ironclad', relic='none', batch_index=0)
```

### Patch ID System

Each simulation run is assigned a unique Patch ID for traceability:

```
PATCH-{YYYYMMDD}-{CHAR}-{SEEDHEX}-{BATCHIDX}-{HASH4}
```

Example: `PATCH-20260202-ICL-0000002A-ALL-1517`

### Output Formats

- **Parquet**: Raw simulation data (per-batch and merged final)
- **Excel (XLSX)**: Summary statistics and deck composition
- **PDF**: Evaluation report with visualizations

## Next Steps

- Read the [Full Help Document](FULL_HELP.md) for detailed API documentation
- Review the [USEME Guide](USEME.md) for helper tool usage
- Explore the [Game Mechanics Reference](GAME_MECHANICS.md) for Slay the Spire rules

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure dependencies are installed with `pip install -r requirements.txt`
2. **Permission errors**: Check write permissions in the output directory
3. **Memory issues**: Reduce `--batch-size` or `--workers` for large simulations

### Getting Help

- Check the [Full Help Document](FULL_HELP.md)
- Open an issue on GitHub
- Review the test files for usage examples
