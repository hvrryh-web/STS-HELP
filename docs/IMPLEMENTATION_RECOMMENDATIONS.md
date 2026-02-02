# Implementation Recommendations: Creating Competitive Edge

**Document Purpose**: Actionable recommendations for improving model accuracy and creating competitive differentiation.

**Last Updated**: 2026-02-02

---

## Quick Reference: Priority Actions

| Priority | Action | Impact | Effort | ROI |
|----------|--------|--------|--------|-----|
| **P0** | Ground Truth Calibration | Critical | 15h | 🌟🌟🌟🌟🌟 |
| **P0** | Complete Card Database | High | 40h | 🌟🌟🌟🌟 |
| **P0** | Enemy Script Accuracy | High | 40h | 🌟🌟🌟🌟 |
| **P1** | AI Lookahead Improvement | High | 30h | 🌟🌟🌟🌟 |
| **P1** | Synergy Detection System | Medium | 20h | 🌟🌟🌟 |
| **P2** | Full Run Simulation | High | 80h | 🌟🌟🌟 |

---

## Recommendation 1: Ground Truth Calibration Pipeline

**Goal**: Ensure simulation results match real gameplay outcomes.

### Step 1: Collect Reference Data

```python
# data/ground_truth/community_stats.json
{
  "source": "spirelogs.com + reddit surveys + spirestats",
  "sample_size": 50000,
  "date_collected": "2026-02-01",
  "metrics": {
    "Ironclad": {
      "A0": {"win_rate": 0.82, "win_rate_ci": [0.80, 0.84]},
      "A20": {"win_rate": 0.12, "win_rate_ci": [0.10, 0.14]}
    },
    "Silent": {
      "A0": {"win_rate": 0.78, "win_rate_ci": [0.76, 0.80]},
      "A20": {"win_rate": 0.11, "win_rate_ci": [0.09, 0.13]}
    },
    "Defect": {
      "A0": {"win_rate": 0.76, "win_rate_ci": [0.74, 0.78]},
      "A20": {"win_rate": 0.10, "win_rate_ci": [0.08, 0.12]}
    },
    "Watcher": {
      "A0": {"win_rate": 0.85, "win_rate_ci": [0.83, 0.87]},
      "A20": {"win_rate": 0.18, "win_rate_ci": [0.15, 0.21]}
    }
  }
}
```

### Step 2: Automated Calibration Test

```python
# tests/test_calibration.py
import pytest
from validation_harness import run_calibration

def test_win_rate_within_tolerance():
    """Ensure simulated win rates match ground truth."""
    ground_truth = load_ground_truth()
    
    for character in ['Ironclad', 'Silent', 'Defect', 'Watcher']:
        result = run_calibration(character, runs=10000)
        
        gt = ground_truth[character]['A0']
        assert gt['win_rate_ci'][0] <= result.win_rate <= gt['win_rate_ci'][1], \
            f"{character} win rate {result.win_rate:.2%} outside expected range"
```

### Step 3: Continuous Calibration Monitoring

Add to CI pipeline:
```yaml
# .github/workflows/calibration.yml
name: Weekly Calibration
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  calibrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run calibration
        run: python validation_harness.py --runs 5000 --output calibration.json
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: calibration-${{ github.run_id }}
          path: calibration.json
```

---

## Recommendation 2: Data-Driven Card System

**Goal**: Replace hardcoded cards with JSON-driven definitions.

### Card Effect Schema

```python
# sts_sim/card_loader.py
from dataclasses import dataclass
from typing import List, Dict, Any
import json

@dataclass
class CardEffect:
    """Composable card effect."""
    type: str  # damage, block, apply_debuff, draw, etc.
    value: int
    target: str = "enemy"  # enemy, self, all_enemies, random
    scaling: str = "none"  # strength, dexterity, focus
    multiplier: float = 1.0
    condition: str = "none"  # always, if_vulnerable, stance_wrath

def load_cards(path: str) -> Dict[str, Card]:
    """Load cards from JSON definition."""
    with open(path) as f:
        card_data = json.load(f)
    
    cards = {}
    for card_id, data in card_data.items():
        effects = [CardEffect(**e) for e in data['effects']]
        cards[card_id] = Card(
            name=data['name'],
            cost=data['cost'],
            card_type=CardType(data['type']),
            effects=effects,
            upgraded_effects=[CardEffect(**e) for e in data.get('upgraded_effects', [])],
            keywords=data.get('keywords', [])
        )
    return cards
```

### JSON Card Definition Format

```json
{
  "heavy_blade": {
    "name": "Heavy Blade",
    "character": "Ironclad",
    "type": "attack",
    "rarity": "common",
    "cost": 2,
    "effects": [
      {"type": "damage", "value": 14, "scaling": "strength", "multiplier": 3}
    ],
    "upgraded_effects": [
      {"type": "damage", "value": 14, "scaling": "strength", "multiplier": 5}
    ],
    "keywords": ["heavy"],
    "synergies": ["strength", "limit_break", "spot_weakness"]
  },
  "demon_form": {
    "name": "Demon Form",
    "character": "Ironclad",
    "type": "power",
    "rarity": "rare",
    "cost": 3,
    "effects": [
      {"type": "apply_power", "power": "demon_form", "value": 2}
    ],
    "upgraded_effects": [
      {"type": "apply_power", "power": "demon_form", "value": 3}
    ],
    "keywords": ["scaling"],
    "synergies": ["heavy_blade", "limit_break"]
  }
}
```

---

## Recommendation 3: Enemy Script System

**Goal**: Accurate enemy behavior modeling with state machines.

### Enemy Script Schema

```python
# sts_sim/enemy_script.py
from dataclasses import dataclass
from typing import List, Dict, Callable

@dataclass
class IntentPattern:
    """Single intent in enemy pattern."""
    intent: str  # attack, buff, debuff, etc.
    damage: int = 0
    hits: int = 1
    block: int = 0
    buff_type: str = ""
    buff_value: int = 0
    probability: float = 1.0
    condition: str = "always"  # always, first_turn, hp_below_50, etc.

@dataclass
class EnemyScript:
    """Complete enemy behavior definition."""
    name: str
    base_hp: tuple[int, int]
    ascension_hp: tuple[int, int]
    patterns: List[List[IntentPattern]]  # Pattern groups
    special_mechanics: Dict[str, Any]
    
    def get_intent(self, turn: int, state: Dict) -> IntentPattern:
        """Get intent for current turn based on state."""
        # Implementation based on pattern probabilities and conditions
        pass
```

### JSON Enemy Definition

```json
{
  "gremlin_nob": {
    "name": "Gremlin Nob",
    "type": "elite",
    "act": 1,
    "hp_ranges": {
      "base": [82, 86],
      "ascension_8": [85, 90]
    },
    "mechanics": {
      "enrage": {
        "trigger": "player_plays_skill",
        "effect": "gain_strength",
        "value": 2
      }
    },
    "pattern": [
      {
        "name": "bellow",
        "probability": 1.0,
        "condition": "turn_1",
        "intent": "buff",
        "buff": {"type": "strength", "value": 2}
      },
      {
        "name": "skull_bash",
        "probability": 0.33,
        "condition": "not_consecutive",
        "intent": "attack_debuff",
        "damage": 6,
        "debuff": {"type": "vulnerable", "stacks": 2}
      },
      {
        "name": "rush",
        "probability": 0.67,
        "intent": "attack",
        "damage": 14
      }
    ]
  }
}
```

---

## Recommendation 4: Synergy Detection Algorithm

**Goal**: Quantify card/relic synergies for better evaluation.

### Synergy Matrix

```python
# sts_sim/synergy.py
import numpy as np
from typing import Dict, List, Tuple

class SynergyCalculator:
    """Calculate deck synergy scores."""
    
    # Synergy pairs: (card_a, card_b) -> bonus multiplier
    SYNERGY_PAIRS = {
        # Ironclad Strength
        ("limit_break", "heavy_blade"): 2.0,
        ("limit_break", "sword_boomerang"): 1.8,
        ("demon_form", "heavy_blade"): 1.5,
        ("spot_weakness", "heavy_blade"): 1.3,
        
        # Silent Poison
        ("catalyst", "noxious_fumes"): 2.5,
        ("catalyst", "deadly_poison"): 2.0,
        ("envenom", "blade_dance"): 1.5,
        ("corpse_explosion", "catalyst"): 2.0,
        
        # Defect Orb
        ("consume", "defragment"): 1.5,
        ("loop", "frost_orb"): 1.5,
        ("echo_form", "meteor_strike"): 2.0,
        
        # Silent Shiv
        ("accuracy", "blade_dance"): 2.0,
        ("after_image", "cloak_and_dagger"): 1.8,
        ("finisher", "blade_dance"): 1.5,
        
        # Watcher Stance
        ("mental_fortress", "rushdown"): 2.0,
        ("flurry_of_blows", "empty_mind"): 1.5,
    }
    
    def calculate_deck_synergy(self, deck: List[str]) -> float:
        """Calculate total synergy score for a deck."""
        total = 0.0
        deck_set = set(deck)
        
        for (card_a, card_b), bonus in self.SYNERGY_PAIRS.items():
            if card_a in deck_set and card_b in deck_set:
                count_a = deck.count(card_a)
                count_b = deck.count(card_b)
                total += bonus * min(count_a, count_b)
        
        return total
    
    def evaluate_card_addition(
        self, 
        deck: List[str], 
        candidate: str
    ) -> float:
        """Evaluate synergy gain from adding a card."""
        current_synergy = self.calculate_deck_synergy(deck)
        new_synergy = self.calculate_deck_synergy(deck + [candidate])
        return new_synergy - current_synergy
```

---

## Recommendation 5: Enhanced AI with Lookahead

**Goal**: Improve decision quality with multi-turn planning.

### Two-Turn Lookahead

```python
# sts_sim/ai_lookahead.py
from typing import List, Tuple
import numpy as np

class LookaheadAI:
    """AI with 2-turn lookahead evaluation."""
    
    def __init__(self, depth: int = 2, samples: int = 10):
        self.depth = depth
        self.samples = samples
    
    def select_action(
        self,
        state: GameState,
        rng: np.random.Generator
    ) -> Tuple[str, float]:
        """Select best action with lookahead."""
        playable = state.get_playable_cards()
        
        if not playable:
            return "end_turn", 0.0
        
        best_action = None
        best_value = float('-inf')
        
        for card in playable:
            value = self._evaluate_with_lookahead(state, card, rng)
            if value > best_value:
                best_value = value
                best_action = card
        
        return best_action, best_value
    
    def _evaluate_with_lookahead(
        self,
        state: GameState,
        action: str,
        rng: np.random.Generator
    ) -> float:
        """Evaluate action with Monte Carlo sampling of future."""
        total_value = 0.0
        
        for _ in range(self.samples):
            # Clone state
            sim_state = state.clone()
            sim_rng = np.random.default_rng(rng.integers(2**31))
            
            # Apply action
            sim_state.play_card(action)
            
            # Simulate 2 turns
            for turn in range(self.depth):
                value = self._simulate_turn(sim_state, sim_rng)
                total_value += value * (0.9 ** turn)  # Discount factor
        
        return total_value / self.samples
    
    def _simulate_turn(
        self,
        state: GameState,
        rng: np.random.Generator
    ) -> float:
        """Simulate one turn with heuristic policy."""
        # Use fast heuristic for simulation
        while state.energy > 0:
            card = self._heuristic_select(state)
            if card is None:
                break
            state.play_card(card)
        
        state.end_turn()
        
        # Return state value estimate
        return self._estimate_state_value(state)
```

---

## Recommendation 6: Speed Optimization

**Goal**: Increase simulation throughput 10x.

### Current Bottlenecks

| Operation | Current Time | Target Time |
|-----------|--------------|-------------|
| Deck shuffle | 0.1ms | 0.01ms |
| Card evaluation | 0.5ms | 0.05ms |
| Enemy intent | 0.1ms | 0.01ms |
| State copy | 0.2ms | 0.02ms |

### Optimization Strategies

```python
# 1. Use numpy arrays instead of lists
deck = np.array([card_id_1, card_id_2, ...], dtype=np.int16)

# 2. Pre-allocate state arrays
class FastCombatState:
    __slots__ = ['hp', 'block', 'energy', 'deck', 'hand', 'discard']
    
    def __init__(self):
        self.deck = np.zeros(100, dtype=np.int16)
        self.hand = np.zeros(10, dtype=np.int16)
        # ...

# 3. Compile hot paths with Numba
from numba import jit

@jit(nopython=True)
def fast_damage_calc(base: int, strength: int, vulnerable: bool) -> int:
    damage = base + strength
    if vulnerable:
        damage = int(damage * 1.5)
    return damage

# 4. Batch simulations with vectorization
def batch_simulate(n_runs: int, seeds: np.ndarray) -> np.ndarray:
    """Run many simulations in parallel."""
    results = np.zeros((n_runs, 4))  # win, turns, damage, hp
    
    for i in range(n_runs):
        results[i] = single_simulate(seeds[i])
    
    return results
```

---

## Recommendation 7: Competitive Edge - Patch Analysis Pipeline

**Goal**: Rapid balance analysis on game updates.

### Automated Patch Detection

```python
# tools/patch_monitor.py
import requests
from datetime import datetime

class PatchMonitor:
    """Monitor for Slay the Spire patch notes."""
    
    STEAM_API_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
    APP_ID = "646570"
    
    def check_for_patches(self) -> List[Dict]:
        """Check for recent patches."""
        response = requests.get(
            self.STEAM_API_URL,
            params={"appid": self.APP_ID, "count": 10}
        )
        return self._parse_patch_notes(response.json())
    
    def generate_analysis(self, patch_data: Dict) -> Dict:
        """Generate balance analysis for patch."""
        changes = self._extract_changes(patch_data)
        
        # Update card/relic definitions
        self._apply_changes(changes)
        
        # Run before/after simulations
        before = self._run_baseline(n=10000)
        after = self._run_current(n=10000)
        
        # Generate delta report
        return {
            "patch_id": patch_data['id'],
            "date": datetime.now().isoformat(),
            "changes": changes,
            "impact": {
                "win_rate_delta": after['win_rate'] - before['win_rate'],
                "affected_archetypes": self._identify_affected(changes)
            }
        }
```

---

## Recommendation 8: API for Real-Time Card Evaluation

**Goal**: Expose simulation capabilities for external use.

### FastAPI Service

```python
# api/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="STS Card Evaluator API")

class DeckState(BaseModel):
    cards: List[str]
    relics: List[str]
    floor: int
    hp: int
    max_hp: int
    ascension: int = 0

class CardChoice(BaseModel):
    card: str
    delta_win_rate: float
    synergy_score: float
    reasoning: str

@app.post("/evaluate_rewards")
async def evaluate_rewards(
    state: DeckState,
    options: List[str]
) -> List[CardChoice]:
    """Evaluate card reward options."""
    results = []
    
    for card in options:
        delta = simulator.evaluate_addition(state.dict(), card)
        synergy = synergy_calc.evaluate_card_addition(state.cards, card)
        
        results.append(CardChoice(
            card=card,
            delta_win_rate=delta,
            synergy_score=synergy,
            reasoning=generate_reasoning(card, state)
        ))
    
    return sorted(results, key=lambda x: x.delta_win_rate, reverse=True)
```

---

## Implementation Timeline

### Week 1-2: Foundation
- [ ] Create ground_truth.json with community data
- [ ] Implement JSON card loader
- [ ] Convert existing cards to JSON format

### Week 3-4: Core Improvements
- [ ] Implement 10 high-priority cards per character
- [ ] Add enemy script system
- [ ] Implement Gremlin Nob with exact behavior

### Week 5-6: Intelligence
- [ ] Implement synergy calculator
- [ ] Add 2-turn lookahead AI
- [ ] Optimize simulation speed

### Week 7-8: Polish & Edge
- [ ] Calibration pipeline with CI
- [ ] Patch monitoring system
- [ ] API prototype

---

## Success Metrics

| Metric | Current | Week 4 | Week 8 |
|--------|---------|--------|--------|
| Card coverage | 15% | 50% | 80% |
| Win rate accuracy | ±20% | ±10% | ±5% |
| Simulation speed | 100/s | 500/s | 2000/s |
| Synergy detection | None | Basic | Complete |
| API availability | No | No | Yes |

---

## Appendix: Quick Wins (< 4 hours each)

1. **Add Bash upgrade effects** - 10 damage, 3 Vulnerable
2. **Implement Neutralize upgrade** - 2 Weak instead of 1
3. **Add Vulnerable calculation to all damage** - Currently missing in some paths
4. **Log simulation statistics** - Track turn distributions
5. **Add --verbose flag** - Better debugging output
6. **Create benchmark suite** - Measure optimization impact

---

**END OF RECOMMENDATIONS**
