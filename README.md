# STS-HELP
Slay the Spire Game Assistant-Helper, Agent Environments & Knowledge Database & Tools

## Overview

This repository provides a production-grade simulation environment for Slay the Spire characters. It includes:

- **Deterministic RNG** via `numpy.random.SeedSequence` for reproducible runs
- **Explicit deck/hand/discard semantics** with hand limit and reshuffle mechanics
- **Intent-aware defensive play** with block and damage modeling
- **Character engines** for Ironclad, Silent, Defect, and Watcher
- **Parallel batch execution** with manifest-based resume
- **Parquet output** with canonical merging
- **Excel and PDF reporting** with Patch ID traceability
- **Decision-value metrics** (EV, PV, RV, APV, UPV, GGV, SGV, CGV, ATV, JV)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Run Unit Tests

```bash
pytest tests/ -v
```

### Run Simulation

```bash
python orchestrator_unified.py --seed 42 --runs 5000 --batch-size 500 --workers 8 --characters Ironclad
```

### Generate Reports

```bash
python -c "import reporting; reporting.generate_excel('unified_outputs', 'PATCH-ID-HERE')"
python -c "import reporting; reporting.generate_pdf('unified_outputs', 'PATCH-ID-HERE')"
```

### Run Calibration

```bash
python validation_harness.py --characters Ironclad Silent Defect Watcher --runs 1000
```

## Architecture

### Components

1. **seed_utils.py** - Deterministic child RNGs via SeedSequence
2. **engine_common.py** - Data models (Card, PlayerState, EnemyState), deck/hand utilities
3. **ironclad_engine.py** - Ironclad simulation with strength scaling
4. **silent_engine.py** - Silent simulation with poison mechanics
5. **defect_engine.py** - Defect simulation with orb mechanics
6. **watcher_engine.py** - Watcher simulation with stance mechanics
7. **orchestrator_unified.py** - Parallel batch runner with manifest resume
8. **reporting.py** - Excel and PDF report generation
9. **validation_harness.py** - Calibration and validation

### Patch ID System

Each simulation run is assigned a unique Patch ID:

```
PATCH-{YYYYMMDD}-{CHAR}-{SEEDHEX}-{BATCHIDX}-{HASH4}
```

- `YYYYMMDD` - Date of run
- `CHAR` - Character code (ICL, SNT, DFT, WTR)
- `SEEDHEX` - Root seed in hex (8 chars)
- `BATCHIDX` - Batch index or "ALL" for merged final
- `HASH4` - Last 4 hex of SHA-1 hash for uniqueness

## Decision Metrics

The simulation computes the following decision-value metrics:

| Metric | Description |
|--------|-------------|
| EV | Estimated Value - baseline expected contribution |
| PV | Prediction Value - model-predicted future value |
| RV | Return Value - realized return observed in simulation |
| NPV | Negative Predictive Value - expected downside |
| APV | Adjusted Predictive Value - PV adjusted by observed RV bias |
| UPV | Updated Prediction Value - APV after Bayesian update |
| GGV | Greed God Value - PV weighted by upside tail |
| SGV | Scared God Value - NPV weighted by downside tail |
| CGV | Content God Value - PV penalized by variance |
| ATV | Ambitious Transcendent Value - PV scaled by win probability |
| JV | Jackpot Value - PV of rare high-reward paths |

## Resolved Issues

The implementation addresses the following gaps from the specification:

- **G1 (RNG determinism)**: Resolved via `SeedSequence` in `seed_utils.py`
- **G2 (Deck/hand fidelity)**: Resolved with explicit DeckState in `engine_common.py`
- **G3 (Block/defense modeling)**: Resolved with intent-aware play in character engines
- **G4 (Artifact semantics)**: Standardized - artifact consumes one application event
- **G5 (Relic acquisition)**: Configurable relic parameter in simulation
- **G6 (Output integrity)**: Per-batch Parquet files with atomic merge
- **G7 (Statistical calibration)**: Validation harness with reservoir sampling
- **G8 (Decision search depth)**: Card value evaluation with limited lookahead

## License

See LICENSE file for details.
