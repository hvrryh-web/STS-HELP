# STS-HELP
Slay the Spire Game Assistant-Helper, Agent Environments & Knowledge Database & Tools

## Overview

This repository provides a comprehensive knowledge base and production-grade simulation environment for Slay the Spire. It serves as a canonical reference for ChatGPT agents and includes:

### Knowledge Base
- **📚 Game Data**: Complete card, relic, enemy, and keyword data in JSON format
- **📖 Verified Mechanics**: Cross-referenced and verified game rules from official sources
- **🎮 Quick Start Guide**: Get up and running quickly
- **📋 Full Documentation**: Comprehensive API and usage documentation

### Simulation Framework
- **Deterministic RNG** via `numpy.random.SeedSequence` for reproducible runs
- **Explicit deck/hand/discard semantics** with hand limit and reshuffle mechanics
- **Intent-aware defensive play** with block and damage modeling
- **Character engines** for Ironclad, Silent, Defect, and Watcher
- **Parallel batch execution** with manifest-based resume
- **Parquet output** with canonical merging
- **Excel and PDF reporting** with Patch ID traceability
- **Decision-value metrics** (EV, PV, RV, APV, UPV, GGV, SGV, CGV, ATV, JV)

---

## 📚 Knowledge Base Structure

```
docs/
├── QUICK_START.md          # Quick start guide
├── FULL_HELP.md            # Complete API documentation
├── USEME.md                # Helper tool reference
├── GAME_MECHANICS.md       # Game rules reference
└── VERIFIED_GAME_DATA.md   # Cross-verified game data

data/
├── cards/
│   ├── ironclad_cards.json # All Ironclad cards
│   ├── silent_cards.json   # All Silent cards
│   ├── defect_cards.json   # All Defect cards
│   └── watcher_cards.json  # All Watcher cards
├── relics/
│   └── relics.json         # All relics by category
├── enemies/
│   └── enemies.json        # Enemy stats and patterns
└── keywords/
    └── keywords.json       # Game keyword definitions
```

### Key Documentation Links

| Document | Description |
|----------|-------------|
| [Quick Start](docs/QUICK_START.md) | Get started in 5 minutes |
| [Full Help](docs/FULL_HELP.md) | Complete API reference |
| [USEME Guide](docs/USEME.md) | Command-line examples |
| [Game Mechanics](docs/GAME_MECHANICS.md) | Verified game rules |
| [Verified Data](docs/VERIFIED_GAME_DATA.md) | Cross-referenced data source |

---

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

---

## Character Quick Reference

| Character | HP | Energy | Starter Relic | Playstyle |
|-----------|-----|--------|---------------|-----------|
| **Ironclad** | 80 | 3 | Burning Blood (+6 HP end combat) | Strength scaling, self-damage |
| **Silent** | 70 | 3 | Ring of the Snake (+2 draw turn 1) | Poison, shivs, discard synergy |
| **Defect** | 75 | 3 | Cracked Core (channel Lightning) | Orbs, Focus scaling |
| **Watcher** | 72 | 3 | Pure Water (add Miracle) | Stances, Mantra |

---

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

---

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

---

## Verified Data Sources

All game data in this repository has been cross-referenced with:

- [Slay the Spire Wiki (Fandom)](https://slay-the-spire.fandom.com/)
- [SlayTheSpire.gg](https://www.slaythespire.gg/)
- [SlayTheSpire.info](https://slaythespire.info/)
- Official game client (v2.3+)

See [VERIFIED_GAME_DATA.md](docs/VERIFIED_GAME_DATA.md) for detailed verification notes.

---

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

---

## License

See LICENSE file for details.
