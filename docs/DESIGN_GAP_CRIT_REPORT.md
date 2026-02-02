# Design Gap CRIT Report

**CRIT**: Critical Review and Improvement Tracking

**Document Version**: 1.0  
**Last Updated**: 2026-02-02  
**Status**: Active Development

---

## Executive Summary

This document provides a comprehensive critical analysis of the STS-HELP simulation system, identifying design gaps, model accuracy issues, and opportunities to create competitive advantages. The analysis is structured around three key areas:

1. **Fidelity Gaps**: Mechanics not yet modeled that affect simulation accuracy
2. **Effectiveness Gaps**: Algorithmic weaknesses limiting optimization quality  
3. **Edge Opportunities**: Unique differentiators for competitive advantage

### Current System Status

| Component | Status | Fidelity Level |
|-----------|--------|----------------|
| Deterministic RNG | ✅ Complete | 100% |
| Deck/Hand/Discard | ✅ Complete | 95% |
| Provenance Tracking | ✅ Complete | 100% |
| Encounter Suite | ✅ Complete | 80% |
| Paired Simulation | ✅ Complete | 90% |
| Card Database | ⚠️ Partial | 40% |
| Relic Effects | ⚠️ Partial | 30% |
| Enemy Scripts | ⚠️ Partial | 25% |
| Full Run Simulation | ❌ Missing | 0% |

---

## Section 1: Fidelity Gaps (G1-G12)

### G1: Incomplete Card Effect Modeling

**Severity**: 🔴 Critical  
**Impact**: High - Cards are the primary decision space

**Current State**:
- Starter deck cards implemented
- ~20 additional cards per character
- ~85% of card pool NOT modeled

**Missing High-Impact Cards**:

| Character | Missing Cards | Priority |
|-----------|---------------|----------|
| Ironclad | Demon Form, Offering, Reaper, Barricade | P0 |
| Silent | Wraith Form, Malaise, Catalyst, Corpse Explosion | P0 |
| Defect | Echo Form, Seek, Creative AI, Biased Cognition | P0 |
| Watcher | Omniscience, Vault, Lesson Learned, Brilliance | P0 |

**Effect Categories Not Modeled**:
- [ ] Retain mechanic
- [ ] Scry mechanic (Watcher)
- [ ] Multi-target attacks
- [ ] Card duplication (Echo Form)
- [ ] Cost modification (Snecko Eye, Corruption)
- [ ] Conditional exhaust
- [ ] Cards that add cards (e.g., Steam Barrier → Claw)

**Recommendation**:
```
PRIORITY: P0
EFFORT: 20-40 hours
ACTION: Implement data-driven card effect system with:
  - Effect registry with composable components
  - JSON-defined card effects for easy expansion
  - Test coverage per card effect type
```

---

### G2: Relic Effects Not Modeled

**Severity**: 🔴 Critical  
**Impact**: High - Relics fundamentally change strategy

**Current State**:
- Starter relics defined but not simulated
- Boss relics not implemented
- Relic synergies absent

**Missing High-Impact Relics**:

| Tier | Relic | Effect | Priority |
|------|-------|--------|----------|
| Boss | Snecko Eye | Confuse + draw 2 | P0 |
| Boss | Runic Pyramid | Keep hand | P0 |
| Boss | Dead Branch | Exhaust → random card | P0 |
| Boss | Fusion Hammer | No upgrades + 1 energy | P1 |
| Common | Bag of Preparation | Draw 2 on turn 1 | P1 |
| Uncommon | Art of War | Extra energy if no attacks | P1 |

**Relic Categories**:
```
Category              Implemented  Total  Coverage
─────────────────────────────────────────────────
Starter Relics        4/4          4      100%
Common Relics         0/28         28     0%
Uncommon Relics       0/37         37     0%
Rare Relics           0/23         23     0%
Boss Relics           0/21         21     0%
Shop Relics           0/15         15     0%
Event Relics          0/15         15     0%
─────────────────────────────────────────────────
TOTAL                 4/143        143    2.8%
```

**Recommendation**:
```
PRIORITY: P0
EFFORT: 30-50 hours
ACTION: Implement relic hook system:
  - Lifecycle hooks: combat_start, turn_start, turn_end, card_play, etc.
  - Passive vs. active relic distinction
  - Relic counter system (e.g., Nunchaku, Shuriken)
  - Synergy tracking for optimization
```

---

### G3: Enemy AI Scripts Missing

**Severity**: 🔴 Critical  
**Impact**: Severe - Enemy behavior determines combat dynamics

**Current State**:
- 5 canonical encounter proxies implemented
- Approximate intent patterns (not exact game logic)
- No actual enemy scripts from game

**Missing Critical Enemies**:

| Act | Enemy/Elite/Boss | Behavior Complexity | Priority |
|-----|------------------|---------------------|----------|
| 1 | Gremlin Nob | Skill trigger + Bellow | P0 |
| 1 | Lagavulin | Asleep phase + Siphon | P0 |
| 1 | Slime Boss | Split mechanic | P0 |
| 2 | Book of Stabbing | Multi-hit scaling | P1 |
| 2 | The Champ | Phase switching | P1 |
| 3 | Awakened One | Curiosity + Second form | P1 |
| 3 | Time Eater | 12-card counter | P0 |
| 3 | Donu & Deca | Multi-target coordination | P1 |

**Enemy Script Requirements**:
1. Intent probability tables (game-accurate)
2. State-dependent behavior (HP thresholds, counters)
3. Special mechanics (Nob's rage, Time Eater's counter)
4. Accurate damage/block values by Ascension level

**Recommendation**:
```
PRIORITY: P0
EFFORT: 40-60 hours
ACTION: Implement enemy script system:
  - Enemy state machine per enemy type
  - Intent selection with game-accurate probabilities
  - Phase transitions for bosses
  - Data file format: JSON with state transitions
```

---

### G4: Ascension Modifiers Not Implemented

**Severity**: 🟡 High  
**Impact**: Medium - Calibration depends on difficulty level

**Current State**:
- Ascension 0 modeled
- No Ascension modifiers applied

**Ascension Effects (Priority)**:

| Level | Effect | Implementation Effort |
|-------|--------|----------------------|
| A1 | Elites more likely | Low |
| A2 | Normal enemies harder | Low |
| A3 | First boss is stronger | Low |
| A4 | Lose 1 HP after each boss | Low |
| A5 | Heal less at rest sites | Low |
| A6 | Start with Ascender's Bane curse | Medium |
| A7 | Bosses drop worse relics | Low |
| A8 | Enemy HP ranges increase | Medium |
| A9 | Start with 10 less HP | Low |
| A10 | Start with 1 less potion slot | Low |
| A11-17 | Cumulative difficulties | Medium |
| A18-20 | Multiple curses, harder everything | High |

**Recommendation**:
```
PRIORITY: P1
EFFORT: 15-20 hours
ACTION: Implement Ascension modifier system:
  - Configurable ascension level per simulation
  - Enemy HP adjustments (A8+)
  - Curse addition (A6)
  - Starting HP reduction (A9)
  - Impact metrics per Ascension level
```

---

### G5: Potion System Not Modeled

**Severity**: 🟡 High  
**Impact**: Medium - Potions are important tactical tools

**Current State**:
- No potion implementation
- No potion usage in AI

**Missing Potion Features**:
- Potion slots (default 3, Ascension 11 = 2)
- Potion types (41 potions total)
- Potion drop rates
- AI decision for potion usage timing

**High-Impact Potions**:

| Potion | Effect | AI Complexity |
|--------|--------|---------------|
| Fairy in a Bottle | Revive with 30% HP | Auto-trigger |
| Blessing of the Forge | Upgrade all cards in hand | Pre-combat |
| Cultist Potion | +1 Ritual | Simple |
| Fire Potion | Deal 20 damage | Damage threshold |
| Flex Potion | +5 Strength this turn | Last-turn optimization |

**Recommendation**:
```
PRIORITY: P1
EFFORT: 10-15 hours
ACTION: Implement potion system:
  - Potion slot management
  - Potion effect execution
  - AI heuristics for optimal potion timing
  - Combat vs. pre-combat potion distinction
```

---

### G6: Full Run Simulation (Not Just Combat)

**Severity**: 🔴 Critical  
**Impact**: Severe - Current system only models single combats

**Current State**:
- Combat simulation only
- No map pathing
- No card/relic/potion rewards
- No events
- No rest sites
- No shops

**Full Run Components Missing**:

```
Component              Status    Complexity
───────────────────────────────────────────
Map Generation         ❌        Medium
Path Selection AI      ❌        High
Card Rewards           ❌        Medium
Relic Rewards          ❌        Medium
Event Handling         ❌        High
Shop Logic             ❌        Medium
Rest Site Decisions    ❌        Low
Potion Drops           ❌        Low
Gold Management        ❌        Low
Curse Management       ❌        Medium
Key Collection         ❌        Medium
───────────────────────────────────────────
```

**Why This Matters**:
- Card selection during run defines deck strength
- Path selection affects encounter types and rewards
- Events can dramatically alter run trajectory
- Shop purchases are high-impact decisions

**Recommendation**:
```
PRIORITY: P0 (for realistic win-rate calibration)
EFFORT: 80-120 hours
ACTION: Phased implementation:
  Phase 1: Simulate fixed-path runs with static rewards (20h)
  Phase 2: Add card reward selection AI (20h)
  Phase 3: Add map generation and path selection (30h)
  Phase 4: Add events and shops (30h)
  Phase 5: Full Ascension 20 support (20h)
```

---

### G7: Card Upgrade System

**Severity**: 🟡 High  
**Impact**: Medium - Upgrades significantly change card values

**Current State**:
- `upgraded` flag exists on Card dataclass
- No upgrade effects implemented
- No upgrade decision AI

**Missing**:
- Upgraded card effect values
- Rest site upgrade decision logic
- Upgrade priority heuristics
- Upgrade synergy tracking (e.g., Apotheosis)

**High-Value Upgrades**:

| Card | Base Effect | Upgraded Effect | Value Increase |
|------|-------------|-----------------|----------------|
| Demon Form | 2 Strength/turn | 3 Strength/turn | +50% |
| Defragment | 1 Focus | 2 Focus | +100% |
| Wraith Form | 2 Intangible | 3 Intangible | +50% |
| Bash | 8 dmg, 2 Vuln | 10 dmg, 3 Vuln | +25% |
| Neutralize | 1 Weak | 2 Weak | +100% |

**Recommendation**:
```
PRIORITY: P1
EFFORT: 15-20 hours
ACTION: Implement upgrade system:
  - Upgraded effect values in card JSON
  - Upgrade priority algorithm
  - Rest site decision model (upgrade vs. heal)
```

---

### G8: Exhaust Synergies Not Modeled

**Severity**: 🟠 Medium  
**Impact**: Medium - Key to certain archetypes

**Current State**:
- `exhaust` flag exists on cards
- Cards correctly exhaust after play
- No synergy tracking

**Missing Exhaust Synergies**:
- Dead Branch (relic): Exhaust → add random card
- Feel No Pain (power): Exhaust → gain 3 block
- Dark Embrace (power): Exhaust → draw 1 card
- Corruption (power): Skills cost 0, exhaust

**Recommendation**:
```
PRIORITY: P2
EFFORT: 8-10 hours
ACTION: Add exhaust event hooks:
  - on_exhaust callback system
  - Track exhausted card count
  - Dead Branch implementation
```

---

### G9: Power Card Duration/Stacking

**Severity**: 🟠 Medium  
**Impact**: Medium - Powers define scaling strategies

**Current State**:
- Powers play and apply effects
- No distinction between stackable vs. unique powers
- No power removal mechanics

**Missing Power Mechanics**:
- Demon Form stacking (+2 Strength per turn)
- Noxious Fumes stacking (poison all enemies)
- Echo Form (complex duration handling)
- Wraith Form (Intangible decrement)
- Corruption (permanent skill cost change)

**Recommendation**:
```
PRIORITY: P1
EFFORT: 12-15 hours
ACTION: Implement power state system:
  - Power registry per combat
  - Stack vs. unique power classification
  - Turn-start/turn-end power triggers
  - Power removal tracking
```

---

### G10: Multi-Hit Attack Mechanics

**Severity**: 🟠 Medium  
**Impact**: Medium - Many strong cards are multi-hit

**Current State**:
- Some multi-hit effects modeled (in encounter_suite)
- Not consistently applied to player cards

**Multi-Hit Complexity**:
- Strength adds to EACH hit
- Vulnerable multiplies EACH hit
- Pen Nib (relic) doubles only first hit? (need verification)

**Critical Multi-Hit Cards**:

| Card | Character | Hits | Base Damage |
|------|-----------|------|-------------|
| Dagger Spray | Silent | 2 | 4×2 |
| Claw | Defect | 1 (scales) | 3+ |
| Flurry of Blows | Watcher | 1 (returns) | 4 |
| Whirlwind | Ironclad | X | 5 per X |
| Cloak and Dagger | Silent | - | + daggers |

**Recommendation**:
```
PRIORITY: P2
EFFORT: 6-8 hours
ACTION: Standardize multi-hit handling:
  - Strength applies per hit
  - Vulnerable applies per hit
  - Proper rounding per hit
```

---

### G11: X-Cost Cards

**Severity**: 🟠 Medium  
**Impact**: Medium - Key late-game scaling cards

**Current State**:
- Not implemented
- No energy-variable effects

**X-Cost Cards by Character**:

| Character | Card | Effect |
|-----------|------|--------|
| Ironclad | Whirlwind | 5 damage × X to all enemies |
| Silent | Skewer | 7 damage × X |
| Defect | Reinforced Body | 7 block × X |
| Defect | Multicast | Evoke rightmost orb X times |
| Watcher | Brilliance | 12 damage × Mantra spent |

**Recommendation**:
```
PRIORITY: P2
EFFORT: 5-6 hours
ACTION: Add X-cost handling:
  - Consume all remaining energy
  - Scale effects by energy consumed
  - Special case: Chemical X relic (+2 to X)
```

---

### G12: Status Card Effects

**Severity**: 🟡 High  
**Impact**: Medium - Status cards clog deck

**Current State**:
- Wound/Daze defined conceptually
- Not added to deck during combat
- No end-of-turn effects (Burn)

**Status Card Implementation Needs**:

| Status | Source | Effect | Priority |
|--------|--------|--------|----------|
| Wound | Several enemies, Doubt curse | Unplayable | P1 |
| Daze | Sentries, Book of Stabbing | Unplayable, Ethereal | P1 |
| Burn | Hexaghost, Searing Blow interaction | 2 damage at end of turn | P1 |
| Slimed | Slimes | Costs 1, Exhaust | P2 |
| Void | Darklings, Snecko | -1 Energy on draw, Ethereal | P1 |

**Recommendation**:
```
PRIORITY: P1
EFFORT: 8-10 hours
ACTION: Implement status cards:
  - Add status cards to player deck during combat
  - End-of-turn damage effects (Burn)
  - Draw-time effects (Void)
  - Ethereal exhaust at end of turn
```

---

## Section 2: Effectiveness Gaps (E1-E6)

### E1: Greedy Card Selection AI

**Severity**: 🔴 Critical  
**Impact**: Severe - Limits policy quality

**Current State**:
```python
# From ironclad_engine.py
def evaluate_card_value(card, player, enemy, deck_state) -> float:
    # Single-turn greedy evaluation
    # No lookahead
    # No future hand consideration
```

**Problems**:
1. No Monte Carlo Tree Search (MCTS)
2. No multi-turn planning
3. Over-values immediate damage
4. Under-values scaling (Demon Form, Limit Break)
5. No opponent modeling beyond current intent

**Improvement Strategies**:

| Strategy | Complexity | Value Gain |
|----------|------------|------------|
| 2-turn lookahead | Medium | High |
| MCTS (100 rollouts) | High | Very High |
| Learned value function | High | Very High |
| Improved heuristics | Low | Medium |

**Recommendation**:
```
PRIORITY: P0
EFFORT: 40-60 hours
ACTION: Implement layered AI system:
  Layer 1: Improved heuristics (block when needed, setup debuffs)
  Layer 2: 2-turn lookahead with hand prediction
  Layer 3: MCTS for complex decisions (optional)
  Layer 4: Trained policy network (future)
```

---

### E2: No Deck Synergy Modeling

**Severity**: 🟡 High  
**Impact**: High - Synergies define strong decks

**Current State**:
- Cards evaluated independently
- No synergy bonuses
- No archetype detection

**Key Synergies Not Modeled**:

| Archetype | Core Synergy | Impact |
|-----------|--------------|--------|
| Strength Ironclad | Limit Break + Heavy Blade | 2-3x damage |
| Poison Silent | Catalyst + Noxious Fumes | Exponential damage |
| Orb Defect | Consume + Reprogram + Loop | Infinite scaling |
| Shiv Silent | Blade Dance + Accuracy + After Image | Burst + defense |
| Stance Watcher | Mental Fortress + Rushdown | Free cards + block |

**Synergy Calculation Approach**:
```
synergy_bonus(card_a, card_b) = {
    "strength" + "heavy_blade": 0.5 * current_strength,
    "poison" + "catalyst": 0.8 * current_poison,
    "dead_branch" + any_exhaust: 3.0,
    "corruption" + "feel_no_pain": 5.0,
    ...
}
```

**Recommendation**:
```
PRIORITY: P1
EFFORT: 20-25 hours
ACTION: Implement synergy system:
  - Synergy matrix (card × card → bonus)
  - Archetype detection from deck composition
  - Dynamic synergy value that updates during run
  - Use synergy score in card reward selection
```

---

### E3: Reward Function Over-Simplification

**Severity**: 🟡 High  
**Impact**: High - Drives all learning

**Current State**:
```python
reward = (100 if win else 0) - damage_taken - (turns * 0.5)
```

**Problems**:
1. Doesn't distinguish close losses from blowouts
2. Doesn't reward efficient play (overkill discouraged)
3. Turn penalty may discourage setup plays
4. Damage penalty inconsistent across Ascension

**Improved Reward Function**:
```python
def compute_reward(result, config):
    base_reward = 0
    
    # Win bonus with margin
    if result.win:
        base_reward = 100
        # Bonus for HP remaining (survived margin)
        base_reward += min(result.final_hp, 20) * 0.5
        # Efficiency bonus
        if result.turns < 10:
            base_reward += (10 - result.turns) * 2
    else:
        # Loss penalty scaled by how close
        enemy_hp_percent = result.enemy_hp / result.enemy_max_hp
        base_reward = -50 * enemy_hp_percent  # Close loss = less penalty
    
    # Damage penalty (normalized by max HP)
    damage_ratio = result.damage_taken / result.starting_hp
    damage_penalty = damage_ratio * 30
    
    return base_reward - damage_penalty
```

**Recommendation**:
```
PRIORITY: P1
EFFORT: 5-8 hours
ACTION: Refine reward function:
  - Add configurable weights
  - Add margin-based bonuses
  - Add per-character normalization
  - A/B test reward functions
```

---

### E4: Ground Truth Calibration Gap

**Severity**: 🔴 Critical  
**Impact**: Severe - Without ground truth, simulation validity unknown

**Current State**:
- No real game data for comparison
- Win rates not validated
- Turn distributions not validated

**Ground Truth Sources**:

| Source | Data Available | Effort to Obtain |
|--------|----------------|------------------|
| SpireStats (community) | Win rates by Ascension | Low |
| spirelogs.com | Detailed run logs | Medium |
| Personal runs | Full replays | Medium |
| Streamer VODs | Strategy patterns | High |

**Calibration Targets Needed**:

| Metric | A0 Target | A20 Target | Tolerance |
|--------|-----------|------------|-----------|
| Ironclad Win Rate | ~80% | ~5-15% | ±5% |
| Silent Win Rate | ~75% | ~5-15% | ±5% |
| Defect Win Rate | ~75% | ~5-15% | ±5% |
| Watcher Win Rate | ~80% | ~10-20% | ±5% |
| Average Turns (combat) | 8-15 | 10-20 | ±20% |
| Average Damage/Combat | 10-25 | 15-30 | ±25% |

**Recommendation**:
```
PRIORITY: P0
EFFORT: 15-20 hours
ACTION: Establish calibration pipeline:
  1. Collect community win rate data (spirestats, reddit surveys)
  2. Create ground_truth.json with expected ranges
  3. Add automated calibration regression test
  4. Alert on >10% deviation from ground truth
  5. Maintain calibration log per Patch ID
```

---

### E5: Limited Variance Reduction

**Severity**: 🟠 Medium  
**Impact**: Medium - Need more runs for significance

**Current State**:
- Paired-seed simulation implemented ✅
- Common Random Numbers (CRN) available ✅
- No importance sampling
- No antithetic variates

**Additional Variance Reduction Techniques**:

| Technique | Implementation Effort | Variance Reduction |
|-----------|----------------------|-------------------|
| Antithetic Variates | Low | 10-30% |
| Importance Sampling | High | 50%+ |
| Control Variates | Medium | 20-40% |
| Stratified Sampling | Low | 10-20% |

**Recommendation**:
```
PRIORITY: P2
EFFORT: 10-15 hours
ACTION: Add stratified sampling:
  - Stratify by starting deck strength
  - Stratify by enemy encounter type
  - Ensure balanced encounter coverage per batch
```

---

### E6: No Policy Distillation

**Severity**: 🟡 High  
**Impact**: High for deployment - No exportable policy

**Current State**:
- Heuristic-only AI
- No learned policy
- No model export

**Policy Learning Roadmap**:

```
Phase 1: Behavioral Cloning (10h)
  - Collect "expert" heuristic decisions
  - Train simple neural network to replicate
  - Baseline for improvement

Phase 2: Policy Gradient (30h)
  - PPO or A2C on combat simulation
  - Reward shaping for learning signal
  - Card-level action space

Phase 3: Full Run Learning (50h)
  - Path selection policy
  - Card reward selection policy
  - Shop decision policy
  - Upgrade priority policy
```

**Recommendation**:
```
PRIORITY: P2 (after full-run simulation)
EFFORT: 50-100 hours
ACTION: Defer until full run simulation complete
```

---

## Section 3: Competitive Edge Opportunities (CE1-CE5)

### CE1: Proprietary Enemy Script Database

**Opportunity Level**: 🌟🌟🌟🌟🌟 (Highest)

**Description**: Build the most accurate enemy behavior database available.

**Why This Creates an Edge**:
- Most simulators use approximate enemy patterns
- Exact script data enables precise strategy optimization
- Community doesn't have centralized verified script data

**Implementation**:
1. Reverse-engineer all enemy scripts from game source/behavior
2. Validate with recorded gameplay
3. Store in structured format (JSON with state machines)
4. Include all Ascension variants
5. Open-source the data (builds community trust + contributions)

**Competitive Moat**: First mover advantage + community investment

---

### CE2: Real-Time Card Value API

**Opportunity Level**: 🌟🌟🌟🌟

**Description**: Provide real-time card evaluation during play.

**Value Proposition**:
- Players use companion app during runs
- App shows expected win rate change per card pick
- Analyzes deck synergies and suggests paths

**Technical Requirements**:
- Sub-second evaluation time
- Deck composition input
- Current floor/HP/relics context
- Output: ranked card recommendations with delta values

**Monetization**: Freemium model with advanced features

---

### CE3: Ascension 20 Streak Optimization

**Opportunity Level**: 🌟🌟🌟🌟

**Description**: Optimize for A20 streak play (most competitive metric).

**Why This Matters**:
- A20 heart kill streaks are the pinnacle of skill
- Current record: ~100+ games (by top players)
- Computational strategy optimization could push this further

**Unique Focus**:
- Minimize variance, not just maximize expected value
- Risk-adjusted path selection
- Floor-by-floor survival probability
- Key decision point identification

**Output**: Strategy guide optimized for consistency, not just win rate

---

### CE4: Patch-Aware Balance Analysis

**Opportunity Level**: 🌟🌟🌟

**Description**: Rapidly analyze balance changes post-patch.

**Use Case**:
- New patch drops
- Within hours, run 100k+ simulations
- Publish win rate impact analysis
- Become the go-to source for patch analysis

**Requirements**:
- Rapid card/relic JSON updates
- Automated simulation pipeline
- Confidence intervals on changes
- Historical comparison

**Community Value**: Establishes authority as analysis leader

---

### CE5: Training Data Generation for RL Research

**Opportunity Level**: 🌟🌟🌟

**Description**: Generate large-scale labeled datasets for RL research.

**Research Applications**:
- Hierarchical reinforcement learning benchmarks
- Multi-objective optimization (win vs. damage vs. time)
- Curriculum learning across Ascension levels
- Transfer learning (character → character)

**Dataset Format**:
```
{
  "state": {deck, hand, relics, hp, enemies, floor},
  "action": {card_played | path_taken | reward_chosen},
  "reward": float,
  "next_state": {...},
  "done": bool,
  "info": {turn, combat_id, run_id}
}
```

**Publication Opportunity**: Academic paper + dataset release

---

## Section 4: Priority Roadmap

### Phase 1: Core Fidelity (4-6 weeks)

| Task | Effort | Dependency |
|------|--------|------------|
| G1: Full card database | 40h | None |
| G2: Relic effect system | 40h | G1 |
| G3: Enemy scripts (Act 1) | 30h | None |
| G12: Status cards | 10h | None |
| E4: Ground truth calibration | 15h | None |

**Phase 1 Deliverable**: Accurate Act 1 simulation with calibration

### Phase 2: Full Combat Fidelity (4-6 weeks)

| Task | Effort | Dependency |
|------|--------|------------|
| G3: Enemy scripts (Act 2-3) | 40h | Phase 1 |
| G4: Ascension modifiers | 15h | None |
| G5: Potion system | 15h | None |
| G7: Card upgrades | 15h | G1 |
| G9: Power duration system | 12h | G1 |

**Phase 2 Deliverable**: Full combat simulation across all Acts

### Phase 3: Full Run Simulation (6-8 weeks)

| Task | Effort | Dependency |
|------|--------|------------|
| G6: Map/path simulation | 40h | Phase 2 |
| G6: Card rewards + selection | 20h | Phase 2 |
| G6: Events | 20h | Phase 2 |
| G6: Shops | 15h | Phase 2 |
| E1: Improved AI | 40h | Phase 2 |

**Phase 3 Deliverable**: Full run simulation A0-A20

### Phase 4: Competitive Edge (Ongoing)

| Task | Effort | Dependency |
|------|--------|------------|
| CE1: Enemy script database | 30h | Phase 2 |
| CE2: Real-time API | 40h | Phase 2 |
| CE4: Patch analysis pipeline | 20h | Phase 3 |
| E6: Policy learning | 80h | Phase 3 |

---

## Section 5: Metrics and Success Criteria

### Fidelity Metrics

| Metric | Current | Phase 1 Target | Phase 3 Target |
|--------|---------|----------------|----------------|
| Card coverage | 15% | 60% | 95% |
| Relic coverage | 3% | 40% | 90% |
| Enemy accuracy | 25% | 70% | 95% |
| Win rate accuracy | Unknown | ±10% | ±3% |
| Turn distribution accuracy | Unknown | ±20% | ±10% |

### Effectiveness Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Simulation speed | ~100 runs/sec | 1000 runs/sec | Benchmark |
| Variance (paired) | High | 50% reduction | Compare unpaired |
| AI win rate (A0) | ~90% | ~85% (realistic) | Compare to human |
| AI win rate (A20) | Unknown | ~10-15% | Compare to community |

### Edge Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Enemy script accuracy | 99%+ | Gameplay validation |
| Patch analysis turnaround | < 24 hours | Release timing |
| Community adoption | 1000+ users | GitHub stars + API calls |

---

## Appendix A: Technical Debt Registry

| Item | Location | Severity | Effort |
|------|----------|----------|--------|
| Magic numbers in heuristics | ironclad_engine.py | Medium | 2h |
| Missing type hints | silent_engine.py | Low | 1h |
| Duplicate card definitions | All engines | Medium | 4h |
| No logging framework | All modules | Low | 2h |
| Missing docstrings | encounter_suite.py | Low | 2h |

---

## Appendix B: Data Sources

### Official Sources
- Slay the Spire Wiki: https://slay-the-spire.fandom.com/
- Official Steam page: https://store.steampowered.com/app/646570/

### Community Sources
- spirelogs.com: Run logging and statistics
- SlayTheSpire.gg: Cards, relics, enemy data
- /r/slaythespire: Community strategy discussion
- Discord: Real-time strategy sharing

### Code Sources
- GitHub MegaCrit repositories (if available)
- Modding community decompiled source analysis
- SaveState analysis tools

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-02 | System | Initial CRIT report |

---

**END OF DOCUMENT**
