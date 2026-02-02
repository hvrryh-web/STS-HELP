# Slay the Spire Simulation - Full Help Document

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Character Engines](#character-engines)
4. [Simulation API](#simulation-api)
5. [Orchestration System](#orchestration-system)
6. [Reporting System](#reporting-system)
7. [Validation Framework](#validation-framework)
8. [Decision Metrics](#decision-metrics)
9. [Data Contracts](#data-contracts)
10. [Extension Guide](#extension-guide)

---

## Architecture Overview

The simulation framework consists of the following layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Layer                        │
│  (orchestrator_unified.py - parallel batch execution)        │
├─────────────────────────────────────────────────────────────┤
│                    Engine Layer                              │
│  ironclad_engine.py | silent_engine.py | defect_engine.py   │
│                    | watcher_engine.py                       │
├─────────────────────────────────────────────────────────────┤
│                    Common Layer                              │
│  engine_common.py (cards, states, mechanics)                 │
│  seed_utils.py (deterministic RNG)                          │
├─────────────────────────────────────────────────────────────┤
│                    Output Layer                              │
│  reporting.py (Excel/PDF) | validation_harness.py           │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### seed_utils.py

Provides deterministic RNG generation using NumPy's `SeedSequence`.

#### Functions

**`make_child_generator(root_seed, archetype, relic, batch_index)`**

Creates a deterministic child RNG.

```python
from seed_utils import make_child_generator

rng = make_child_generator(
    root_seed=42,           # Master seed
    archetype='Ironclad',   # Character name
    relic='burning_blood',  # Relic name or 'none'
    batch_index=0           # Batch identifier
)
```

**`generate_patch_id(date_str, character_code, root_seed, batch_index, metadata)`**

Generates a unique Patch ID for traceability.

```python
from seed_utils import generate_patch_id

patch_id = generate_patch_id(
    date_str='20260202',
    character_code='ICL',
    root_seed=42,
    batch_index=None,  # None = merged final
    metadata={'runs': 1000}
)
# Returns: 'PATCH-20260202-ICL-0000002A-ALL-xxxx'
```

**`get_character_code(character)`**

Maps character name to three-letter code.

```python
from seed_utils import get_character_code

code = get_character_code('Ironclad')  # Returns 'ICL'
```

### engine_common.py

Defines core data models and game mechanics.

#### Data Models

**Card**

```python
from engine_common import Card, CardType

strike = Card(
    name="Strike",
    cost=1,
    card_type=CardType.ATTACK,
    effects={'damage': 6},
    upgraded=False,
    innate=False,
    ethereal=False,
    exhaust=False
)
```

**PlayerState**

```python
from engine_common import PlayerState

player = PlayerState(
    hp=80,
    max_hp=80,
    block=0,
    energy=3,
    max_energy=3,
    strength=0,
    dexterity=0,
    artifact=0,
    poison=0,
    orbs=[],
    orb_slots=3,
    stance='neutral',
    relics=[]
)
```

**EnemyState**

```python
from engine_common import EnemyState, Intent

enemy = EnemyState(
    name="Gremlin Nob",
    hp=82,
    max_hp=82,
    block=0,
    strength=0,
    poison=0,
    vulnerable=0,
    weak=0,
    artifact=0,
    intent=Intent.ATTACK,
    intent_value=14
)
```

**DeckState**

```python
from engine_common import DeckState

deck = DeckState(
    draw_pile=[...],
    hand=[],
    discard_pile=[],
    exhaust_pile=[],
    hand_limit=10
)

# Draw cards
rng = np.random.default_rng(42)
drawn = deck.draw_cards(5, rng)

# Discard
deck.discard_card(card)

# Exhaust
deck.exhaust_card(card)
```

**CombatResult**

```python
from engine_common import CombatResult

result = CombatResult(
    win=True,
    turns=12,
    damage_taken=35,
    final_hp=45,
    enemy_hp=0,
    peak_poison=0,
    peak_strength=4,
    peak_orbs=0,
    cards_played=48
)
```

#### Game Mechanics Functions

**Damage Application**

```python
from engine_common import apply_damage_to_enemy, apply_damage_to_player

# Apply damage considering block, strength, vulnerability
actual_damage = apply_damage_to_enemy(enemy, base_damage=10, player=player)
actual_damage = apply_damage_to_player(player, base_damage=15, enemy=enemy)
```

**Debuff Application**

```python
from engine_common import apply_debuff, apply_poison

# Respects artifact (blocks one application)
success = apply_debuff(enemy, 'vulnerable', amount=2)
success = apply_poison(enemy, amount=5)
```

**Poison Processing**

```python
from engine_common import process_poison_tick, decrement_debuffs

# At end of enemy turn
damage = process_poison_tick(enemy)  # Deals poison damage, decrements
decrement_debuffs(enemy)  # Decrements vulnerable/weak
```

**Starter Deck Creation**

```python
from engine_common import create_starter_deck

deck = create_starter_deck('Ironclad')  # Returns list of Card objects
```

---

## Character Engines

Each character has a dedicated engine module implementing character-specific mechanics.

### Ironclad Engine (`ironclad_engine.py`)

Ironclad focuses on **strength scaling** and **self-damage synergies**.

```python
from ironclad_engine import simulate_run, create_ironclad_player

# Create player
player = create_ironclad_player(relic='burning_blood')

# Run simulation
rng = np.random.default_rng(42)
result = simulate_run(rng, relic='none', enemy_hp=120, max_turns=50)
```

**Ironclad-Specific Cards:**
- Inflame (+2 Strength)
- Heavy Blade (3x strength multiplier)
- Limit Break (double strength)
- Clothesline (damage + weak)
- Shrug It Off (block + draw)

### Silent Engine (`silent_engine.py`)

Silent focuses on **poison stacking** and **shiv generation**.

```python
from silent_engine import simulate_run, create_silent_player

player = create_silent_player(relic='ring_of_the_snake')
result = simulate_run(rng, relic='none', enemy_hp=100, max_turns=50)
```

**Silent-Specific Cards:**
- Deadly Poison (5 poison)
- Catalyst (double poison, exhaust)
- Noxious Fumes (2 poison per turn power)
- Blade Dance (3 shivs)
- Acrobatics (draw 3, discard 1)

### Defect Engine (`defect_engine.py`)

Defect focuses on **orb mechanics** and **focus scaling**.

```python
from defect_engine import simulate_run, create_defect_player

player = create_defect_player(relic='cracked_core')
result = simulate_run(rng, relic='none', enemy_hp=110, max_turns=50)
```

**Orb Types:**
- **Lightning**: Passive 3+focus damage, Evoke 8+focus damage
- **Frost**: Passive 2+focus block, Evoke 5+focus block
- **Dark**: Passive accumulates 6+focus, Evoke deals accumulated
- **Plasma**: Passive none, Evoke grants 2 energy

**Defect-Specific Cards:**
- Ball Lightning (damage + channel lightning)
- Glacier (block + channel 2 frost)
- Defragment (+1 focus)
- Capacitor (+2 orb slots)
- Dualcast (evoke rightmost orb twice)

### Watcher Engine (`watcher_engine.py`)

Watcher focuses on **stance dancing** and **mantra accumulation**.

```python
from watcher_engine import simulate_run, create_watcher_player

player = create_watcher_player(relic='pure_water')
result = simulate_run(rng, relic='none', enemy_hp=105, max_turns=50)
```

**Stances:**
- **Neutral**: No bonuses
- **Wrath**: 2x damage dealt AND taken
- **Calm**: Gain 2 energy when exiting
- **Divinity**: 3x damage, +3 energy, auto-exits

**Watcher-Specific Cards:**
- Eruption (damage + enter Wrath)
- Vigilance (block + enter Calm)
- Prostrate (block + 2 mantra)
- Mental Fortress (block on stance change)
- Tantrum (3 hits + enter Wrath)

---

## Simulation API

### Running Individual Simulations

```python
from ironclad_engine import simulate_run
import numpy as np

rng = np.random.default_rng(42)
result = simulate_run(rng, relic='none', enemy_hp=120, max_turns=50)

print(f"Win: {result.win}")
print(f"Turns: {result.turns}")
print(f"Damage taken: {result.damage_taken}")
print(f"Cards played: {result.cards_played}")
```

### Running Batch Simulations

```python
from orchestrator_unified import run_batch

results = run_batch(
    character='Ironclad',
    relic='none',
    root_seed=42,
    batch_index=0,
    batch_size=100,
    enemy_hp=120,
    max_turns=50
)
```

### Full Orchestrated Run

```python
from orchestrator_unified import run_orchestrator

results = run_orchestrator(
    seed=42,
    runs=5000,
    batch_size=500,
    workers=8,
    characters=['Ironclad', 'Silent', 'Defect', 'Watcher'],
    relics=['none'],
    output_dir='unified_outputs',
    enemy_hp=120,
    max_turns=50
)
```

---

## Orchestration System

### Manifest-Based Resume

The orchestrator tracks progress in `manifest.json`:

```json
{
  "completed_batches": ["Ironclad:0", "Ironclad:1", ...],
  "parameters": {
    "seed": 42,
    "runs": 5000,
    "batch_size": 500
  },
  "start_time": "2026-02-02T10:00:00",
  "last_update": "2026-02-02T10:15:00"
}
```

Resume interrupted runs by re-running with same parameters.

### Parallel Execution

Uses `ProcessPoolExecutor` for parallel batch processing:

```bash
python orchestrator_unified.py --workers 8  # Use 8 CPU cores
```

### Output Structure

```
unified_outputs/
├── Ironclad/
│   ├── batch_0000_PATCH-xxx.parquet
│   ├── batch_0001_PATCH-xxx.parquet
│   └── ...
├── final/
│   └── Ironclad_PATCH-xxx.parquet
└── manifest.json
```

---

## Reporting System

### Excel Report Generation

```python
from reporting import generate_excel

excel_path = generate_excel(
    parquet_dir='unified_outputs',
    patch_id='PATCH-20260202-ICL-0000002A-ALL-1517',
    output_path='report.xlsx'  # Optional
)
```

**Excel Sheets:**
1. **Summary**: Win rates, turns, damage by character
2. **Aggregated Metrics**: EV, PV, APV, GGV, etc.
3. **Deck Composition**: Card slot templates
4. **Raw Sample**: First 100 rows of data
5. **Patch Log**: Metadata and timestamps

### PDF Report Generation

```python
from reporting import generate_pdf

pdf_path = generate_pdf(
    parquet_dir='unified_outputs',
    patch_id='PATCH-20260202-ICL-0000002A-ALL-1517',
    output_path='report.pdf'  # Optional
)
```

**PDF Contents:**
- Executive summary
- Summary statistics table
- Decision metrics table
- Win rate chart
- Damage distribution chart
- Observations and recommendations

---

## Validation Framework

### Calibration

Run calibration to compare against expected baselines:

```python
from validation_harness import run_calibration, run_full_calibration

# Single character
result = run_calibration('Ironclad', runs=1000, seed=42)
print(f"Win rate: {result.win_rate:.2%}")
print(f"95% CI: {result.win_rate_ci}")

# All characters
results = run_full_calibration(
    characters=['Ironclad', 'Silent', 'Defect', 'Watcher'],
    runs_per_char=1000,
    seed=42,
    output_path='calibration.json'
)
```

### Reservoir Sampling

For streaming median computation with bounded memory:

```python
from validation_harness import ReservoirSampler

sampler = ReservoirSampler(k=1000)
for value in stream:
    sampler.add(value)

median = sampler.get_median()
p95 = sampler.get_percentile(95)
```

### Wilson Score Interval

For binomial confidence intervals:

```python
from validation_harness import wilson_score_interval

lower, upper = wilson_score_interval(successes=450, trials=500, z=1.96)
# 95% CI for win rate
```

---

## Decision Metrics

The simulation computes the following decision-value metrics:

| Metric | Formula | Description |
|--------|---------|-------------|
| **EV** | E[reward] | Estimated Value - baseline expected contribution |
| **PV** | 50.0 (baseline) | Prediction Value - model-predicted future value |
| **RV** | E[reward] | Return Value - realized return observed |
| **NPV** | -E[reward \| reward < 0] | Negative Predictive Value - expected downside |
| **APV** | PV + λ(RV - PV) | Adjusted Predictive Value - bias-corrected PV |
| **UPV** | APV | Updated Prediction Value - after Bayesian update |
| **GGV** | P95(reward) | Greed God Value - upside tail value |
| **SGV** | -P5(reward) | Scared God Value - downside tail value |
| **CGV** | APV - β·σ(reward) | Content God Value - variance-penalized |
| **ATV** | APV · P(win) | Ambitious Transcendent Value - win-weighted |
| **JV** | P(high) · E[high] | Jackpot Value - rare high-reward paths |

### Reward Formula

```
reward = win * 100 - damage_taken
```

### Parameter Tuning

```python
from reporting import compute_decision_metrics

metrics = compute_decision_metrics(
    df,
    lambda_param=0.3,  # APV adjustment rate
    beta_param=0.1     # CGV risk penalty
)
```

---

## Data Contracts

### Parquet Schema

```
| Column        | Type    | Description                    |
|---------------|---------|--------------------------------|
| win           | bool    | Combat victory                 |
| turns         | int64   | Turns taken                    |
| damage_taken  | int64   | Total damage to player         |
| final_hp      | int64   | Player HP at end               |
| enemy_hp      | int64   | Enemy HP at end                |
| peak_poison   | int64   | Max poison applied             |
| peak_strength | int64   | Max strength gained            |
| peak_orbs     | int64   | Max orbs channeled             |
| cards_played  | int64   | Total cards played             |
| character     | string  | Character name                 |
| relic         | string  | Relic name                     |
| root_seed     | int64   | Root RNG seed                  |
| batch_index   | int64   | Batch identifier               |
| run_index     | int64   | Global run identifier          |
```

### Manifest Schema

```json
{
  "completed_batches": ["string"],
  "parameters": {
    "seed": "int",
    "runs": "int",
    "batch_size": "int",
    "characters": ["string"],
    "relics": ["string"],
    "enemy_hp": "int",
    "max_turns": "int"
  },
  "start_time": "ISO8601",
  "last_update": "ISO8601"
}
```

---

## Extension Guide

### Adding New Cards

1. Define the card in the character's engine:

```python
IRONCLAD_CARDS['New Card'] = Card(
    name='New Card',
    cost=1,
    card_type=CardType.ATTACK,
    effects={'damage': 10, 'custom_effect': True}
)
```

2. Handle the effect in `play_card`:

```python
if effects.get('custom_effect'):
    # Implement custom logic
    pass
```

3. Update `evaluate_card_value` for AI decision-making.

### Adding New Enemies

Create enemy in `engine_common.py`:

```python
ENEMIES = {
    'Gremlin Nob': EnemyState(name="Gremlin Nob", hp=82, max_hp=82),
    'Lagavulin': EnemyState(name="Lagavulin", hp=112, max_hp=112),
}
```

Implement intent patterns in the character engine's `get_enemy_intent`.

### Adding New Relics

1. Handle in player creation:

```python
if relic == 'new_relic':
    player.max_energy += 1  # Example effect
```

2. Handle combat triggers in `simulate_combat` if needed.

### Adding New Characters

1. Create `new_character_engine.py` following existing engine patterns
2. Add to `get_engine()` in `orchestrator_unified.py`
3. Add starter deck in `engine_common.py`
4. Add character code in `seed_utils.py`
