# USEME - Helper Tool Reference

This guide provides quick-reference examples for common tasks using the STS-HELP simulation framework.

---

## Quick Reference Table

| Task | Command |
|------|---------|
| Run tests | `pytest tests/ -v` |
| Simple simulation | `python orchestrator_unified.py --runs 100` |
| Full calibration | `python validation_harness.py --runs 1000` |
| Generate reports | `python reporting.py unified_outputs PATCH-ID` |

---

## Common Use Cases

### 1. Run a Quick Test Simulation

```bash
# 100 runs for Ironclad only
python orchestrator_unified.py --seed 42 --runs 100 --batch-size 50 --workers 2 --characters Ironclad
```

### 2. Full Character Comparison

```bash
# 5000 runs per character, parallel execution
python orchestrator_unified.py \
    --seed 42 \
    --runs 5000 \
    --batch-size 500 \
    --workers 8 \
    --characters Ironclad Silent Defect Watcher \
    --output-dir comparison_run
```

### 3. Calibration Against Ground Truth

```bash
# Create ground_truth.json first:
echo '{
  "Ironclad": {"win_rate": 0.75},
  "Silent": {"win_rate": 0.70},
  "Defect": {"win_rate": 0.68},
  "Watcher": {"win_rate": 0.72}
}' > ground_truth.json

# Run calibration
python validation_harness.py \
    --characters Ironclad Silent Defect Watcher \
    --runs 2000 \
    --ground-truth ground_truth.json \
    --output calibration_results.json
```

### 4. Generate Reports from Existing Data

```bash
# Get the Patch ID from your simulation output
PATCH_ID="PATCH-20260202-ICL-0000002A-ALL-1517"

# Generate both Excel and PDF
python reporting.py unified_outputs $PATCH_ID
```

### 5. Python Script Examples

#### Single Simulation Run

```python
#!/usr/bin/env python3
"""Run a single combat simulation and print results."""

from ironclad_engine import simulate_run
import numpy as np

rng = np.random.default_rng(42)
result = simulate_run(rng, relic='none', enemy_hp=120)

print(f"Result: {'Victory' if result.win else 'Defeat'}")
print(f"Turns: {result.turns}")
print(f"Damage taken: {result.damage_taken}")
print(f"Final HP: {result.final_hp}")
print(f"Cards played: {result.cards_played}")
```

#### Batch Statistical Analysis

```python
#!/usr/bin/env python3
"""Run 1000 simulations and compute statistics."""

from seed_utils import make_child_generator
from ironclad_engine import simulate_run
import numpy as np

wins = 0
damages = []

for i in range(1000):
    rng = make_child_generator(42, 'Ironclad', 'none', i)
    result = simulate_run(rng)
    
    if result.win:
        wins += 1
    damages.append(result.damage_taken)

print(f"Win rate: {wins/1000:.1%}")
print(f"Mean damage: {np.mean(damages):.1f}")
print(f"Std damage: {np.std(damages):.1f}")
```

#### Custom Deck Testing

```python
#!/usr/bin/env python3
"""Test a custom deck composition."""

from engine_common import Card, CardType, DeckState, PlayerState, EnemyState
from ironclad_engine import simulate_combat
import numpy as np

# Create custom deck
custom_deck = [
    Card("Strike", 1, CardType.ATTACK, {'damage': 6}),
    Card("Strike", 1, CardType.ATTACK, {'damage': 6}),
    Card("Defend", 1, CardType.SKILL, {'block': 5}),
    Card("Defend", 1, CardType.SKILL, {'block': 5}),
    Card("Inflame", 1, CardType.POWER, {'strength': 2}),
    Card("Heavy Blade", 2, CardType.ATTACK, {'damage': 14, 'strength_multiplier': 3}),
]

player = PlayerState(hp=80, max_hp=80, energy=3)
enemy = EnemyState(name="Custom", hp=100, max_hp=100)
rng = np.random.default_rng(42)

result = simulate_combat(player, enemy, custom_deck, rng)
print(f"Win: {result.win}, Turns: {result.turns}")
```

#### Relic Comparison

```python
#!/usr/bin/env python3
"""Compare win rates across different starting relics."""

from seed_utils import make_child_generator
from ironclad_engine import simulate_run

relics = ['none', 'burning_blood', 'snecko_eye']
results = {}

for relic in relics:
    wins = 0
    for i in range(500):
        rng = make_child_generator(42, 'Ironclad', relic, i)
        result = simulate_run(rng, relic=relic)
        if result.win:
            wins += 1
    results[relic] = wins / 500

for relic, rate in results.items():
    print(f"{relic}: {rate:.1%}")
```

---

## CLI Reference

### orchestrator_unified.py

```
usage: orchestrator_unified.py [-h] [--seed SEED] [--runs RUNS]
                               [--batch-size BATCH_SIZE] [--workers WORKERS]
                               [--characters {Ironclad,Silent,Defect,Watcher} ...]
                               [--relics RELICS ...] [--output-dir OUTPUT_DIR]
                               [--enemy-hp ENEMY_HP] [--max-turns MAX_TURNS]

Slay the Spire Unified Orchestrator

options:
  --seed SEED           Root seed (default: 42)
  --runs RUNS           Total runs per character (default: 1000)
  --batch-size SIZE     Runs per batch (default: 100)
  --workers WORKERS     Parallel workers (default: 4)
  --characters CHARS    Characters to simulate (default: Ironclad)
  --relics RELICS       Relics to test (default: none)
  --output-dir DIR      Output directory (default: unified_outputs)
  --enemy-hp HP         Enemy HP (default: 120)
  --max-turns TURNS     Maximum turns (default: 50)
```

### validation_harness.py

```
usage: validation_harness.py [-h] [--characters CHARS ...] [--runs RUNS]
                             [--seed SEED] [--ground-truth PATH]
                             [--output PATH]

STS Simulation Validation Harness

options:
  --characters CHARS    Characters to calibrate (default: Ironclad)
  --runs RUNS           Runs per character (default: 1000)
  --seed SEED           Random seed (default: 42)
  --ground-truth PATH   Path to ground truth JSON
  --output PATH         Output path for results (default: calibration_results.json)
```

### reporting.py

```
usage: reporting.py <parquet_dir> <patch_id>

Generate Excel and PDF reports from simulation data.

positional arguments:
  parquet_dir    Directory containing parquet files
  patch_id       Patch ID for the report
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STS_OUTPUT_DIR` | Default output directory | `unified_outputs` |
| `STS_DEFAULT_SEED` | Default random seed | `42` |
| `STS_MAX_WORKERS` | Max parallel workers | CPU count |

---

## Troubleshooting

### Issue: "No module named 'numpy'"

```bash
pip install -r requirements.txt
```

### Issue: "Permission denied" writing output

```bash
mkdir -p unified_outputs
chmod 755 unified_outputs
```

### Issue: Out of memory

Reduce batch size or workers:
```bash
python orchestrator_unified.py --batch-size 50 --workers 2
```

### Issue: Simulation hangs

Check for infinite loops in card selection by adding max iterations:
```python
max_cards = 100
cards_this_turn = 0
while player.energy > 0 and cards_this_turn < max_cards:
    # ...
    cards_this_turn += 1
```

---

## Integration Examples

### With Pandas

```python
import pandas as pd

# Load simulation results
df = pd.read_parquet('unified_outputs/final/Ironclad_PATCH-xxx.parquet')

# Win rate by batch
print(df.groupby('batch_index')['win'].mean())

# Damage distribution
df['damage_taken'].hist(bins=30)
```

### With Jupyter Notebooks

```python
# In a Jupyter notebook
from IPython.display import display
import pandas as pd

df = pd.read_parquet('unified_outputs/final/Ironclad_PATCH-xxx.parquet')

# Summary statistics
display(df.describe())

# Win rate visualization
df['win'].value_counts().plot.pie(autopct='%1.1f%%')
```

### CI/CD Integration

```yaml
# .github/workflows/simulation.yml
name: Run Simulation

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  simulate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - run: python orchestrator_unified.py --runs 1000
    - uses: actions/upload-artifact@v4
      with:
        name: simulation-results
        path: unified_outputs/
```
