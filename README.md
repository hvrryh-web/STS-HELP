# STS-HELP
Slay the Spire Game Assistant-Helper, Agent Environments & Knowledge Database & Tools

## Overview

This repository provides a comprehensive knowledge base and production-grade simulation environment for Slay the Spire. It serves as a canonical reference for ChatGPT agents and includes:

### Knowledge Base
- **📚 Game Data**: Complete card, relic, enemy, and keyword data in JSON format
- **📖 Verified Mechanics**: Cross-referenced and verified game rules from official sources
- **🎮 Quick Start Guide**: Get up and running quickly
- **📋 Full Documentation**: Comprehensive API and usage documentation
- **🧠 Research Documentation**: Deep dive into strategy, AI/ML research, and quantum economics
- **🛠️ Decision-Support Tools**: Prototype tools for synergy analysis and path optimization

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
├── QUICK_START.md               # Quick start guide
├── FULL_HELP.md                 # Complete API documentation
├── USEME.md                     # Helper tool reference
├── GAME_MECHANICS.md            # Game rules reference
├── VERIFIED_GAME_DATA.md        # Cross-verified game data
├── STS_STRATEGY_RESEARCH.md     # Deep dive into STS mechanics and AI research
├── AI_ML_RESEARCH.md            # Survey of AI/ML academic papers
├── QUANTIZING_ECONOMICS.md      # Quantum economics and decision theory
└── GLOSSARY.md                  # Unified glossary for all topics

data/
├── cards/
│   ├── ironclad_cards.json      # All Ironclad cards
│   ├── silent_cards.json        # All Silent cards
│   ├── defect_cards.json        # All Defect cards
│   └── watcher_cards.json       # All Watcher cards
├── relics/
│   └── relics.json              # All relics by category
├── enemies/
│   └── enemies.json             # Enemy stats and patterns
└── keywords/
    └── keywords.json            # Game keyword definitions

tools/
├── synergy_analyzer.py          # Card/relic synergy analysis tool
├── path_optimizer.py            # Entropy-based path recommendation
└── README.md                    # Tools documentation
```

### Key Documentation Links

| Document | Description |
|----------|-------------|
| [Quick Start](docs/QUICK_START.md) | Get started in 5 minutes |
| [Full Help](docs/FULL_HELP.md) | Complete API reference |
| [USEME Guide](docs/USEME.md) | Command-line examples |
| [Game Mechanics](docs/GAME_MECHANICS.md) | Verified game rules |
| [Verified Data](docs/VERIFIED_GAME_DATA.md) | Cross-referenced data source |

### Research Documentation

| Document | Description |
|----------|-------------|
| [STS Strategy & Research](docs/STS_STRATEGY_RESEARCH.md) | Comprehensive analysis of mechanics, strategy, and AI research |
| [AI/ML Research Survey](docs/AI_ML_RESEARCH.md) | Academic papers on AI/ML in Slay the Spire |
| [Quantizing Economics](docs/QUANTIZING_ECONOMICS.md) | Quantum economics and decision theory |
| [Glossary](docs/GLOSSARY.md) | Unified glossary for all topics |
| [Decision Tools](tools/README.md) | Prototype decision-support tools |

### System Reports

| Document | Description |
|----------|-------------|
| [Design Gap CRIT Report](docs/DESIGN_GAP_CRIT_REPORT.md) | Original critical review of design gaps and opportunities |
| [Modeling System CRIT Report](docs/MODELING_SYSTEM_CRIT_REPORT.md) | Analysis of modeling methods, prediction accuracy, and improvement plan |
| [Verification Report](docs/VERIFICATION_REPORT.md) | Data gaps, assumptions, and validation status for Monte Carlo simulations |

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
10. **simulation_config.py** - Explicit heuristics and variable-driven configuration

### Monte Carlo Test Suites

The simulation system includes two large-batch Monte Carlo test suites for validation:

#### Suite 1: Veracity Tests
- Deterministic reproducibility verification
- Output bounds validation
- Internal consistency checks (no impossible states)
- Metadata logging completeness
- Cross-character validation

#### Suite 2: Stability Tests
- Batch consistency analysis
- Convergence with sample size
- Variance bounds verification
- Failure-tail analysis
- Seed sensitivity testing

Run the Monte Carlo tests:
```bash
pytest tests/test_monte_carlo_simulation.py -v
```

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

## 🧠 Research & Decision-Support Tools

This repository includes comprehensive research documentation and prototype decision-support tools based on academic papers and expert strategy analysis.

### Research Documentation

- **[STS Strategy & Research](docs/STS_STRATEGY_RESEARCH.md)**: Deep dive into game mechanics, strategic archetypes, procedural generation, and the Ascension system
- **[AI/ML Research Survey](docs/AI_ML_RESEARCH.md)**: Comprehensive survey of academic papers including:
  - Neural network path prediction (Malmö University)
  - Entropy and risk analysis (arXiv 2025)
  - Luck vs. skill quantification (IEEE COG 2023)
  - Reinforcement learning applications
- **[Quantizing Economics](docs/QUANTIZING_ECONOMICS.md)**: Application of quantum mechanics concepts to economics and decision theory
  - Quantum Decision Theory (QDT)
  - Superposition, entanglement, and measurement effects
  - Applications to strategic decision-making
- **[Glossary](docs/GLOSSARY.md)**: Unified glossary covering both quantum economics and STS terminology

### Decision-Support Tools

Located in `tools/` directory:

#### Synergy Analyzer (`synergy_analyzer.py`)

Analyzes card and relic synergies to inform deck-building decisions:

```bash
python tools/synergy_analyzer.py
```

Features:
- Identifies active synergies (Strength scaling, Poison, Shivs, Orbs, etc.)
- Calculates synergy scores
- Recommends best cards to add
- Provides strategic deck-building advice

#### Path Optimizer (`path_optimizer.py`)

Recommends optimal map paths using entropy-based heuristics from research:

```bash
python tools/path_optimizer.py
```

Features:
- Evaluates path quality using Shannon entropy
- Balances risk vs. reward based on game state
- Estimates HP costs and expected value
- Based on research showing higher-entropy paths correlate with winning

See [tools/README.md](tools/README.md) for detailed documentation and usage examples.

### Key Research Findings

1. **Higher-Entropy Paths Win**: Research shows winning players take riskier, more diverse paths
2. **Elite Fights Critical**: 2-3 elites per act optimal for relic acquisition despite HP risk
3. **Skill Dominates Luck**: Top players achieve 70-90% win rates through adaptation
4. **Quantum Parallels**: Decision-making under uncertainty in STS mirrors quantum economic principles

### Research References

- [Using machine learning to help find paths through the map in Slay the Spire](https://www.diva-portal.org/smash/get/diva2:1565751/FULLTEXT02.pdf)
- [Analysis of Uncertainty in Procedural Maps in Slay the Spire (arXiv)](https://arxiv.org/html/2504.03918v1)
- [Are You Lucky or Skilled? (IEEE COG 2023)](https://aeau.github.io/assets/papers/2023/andersson2023-cog03.pdf)
- [Slay the Spire: Metrics Driven Design and Balance (GDC Vault)](https://www.gdcvault.com/play/1025731/-Slay-the-Spire-Metrics)
- [Quantum Economics by David Orrell](https://books.google.com/books/about/Quantum_Economics.html?id=9YlZDwAAQBAJ)
- [Quantum propensity in economics (arXiv)](https://arxiv.org/pdf/2103.10938)

---

## License

See LICENSE file for details.
