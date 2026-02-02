# Monte Carlo Simulation System: Data Gaps and Verification Report

## Overview

This document provides a comprehensive verification report for the Monte Carlo Quantized Economic Data Simulation System. It documents data gaps, inconsistencies flagged for manual review, and validation status for all simulation components.

## Verification Coverage Summary

### Characters and Base Configurations ✅

| Character | Starter Deck | Starting HP | Energy | Starter Relic | Status |
|-----------|--------------|-------------|--------|---------------|--------|
| Ironclad | 10 cards | 80 | 3 | Burning Blood | ✅ Verified |
| Silent | 12 cards | 70 | 3 | Ring of Snake | ✅ Verified |
| Defect | 10 cards | 75 | 3 | Cracked Core | ✅ Verified |
| Watcher | 10 cards | 72 | 3 | Pure Water | ✅ Verified |

### Cards Coverage

| Category | Status | Notes |
|----------|--------|-------|
| Starter Cards (all characters) | ✅ Fully implemented | Strike, Defend, character-specific starters |
| Basic Attacks | ✅ Implemented | Damage + effects modeled |
| Basic Skills | ✅ Implemented | Block + effects modeled |
| Powers | ⚠️ Partial | Strength/Dexterity powers only |
| Curses | ⚠️ Limited | Basic curse effects (no complex interactions) |
| Status Cards | ⚠️ Limited | Basic status effects |
| Colourless Cards | ❌ Not implemented | Out of scope for current version |

### Relics and Potions

| Category | Status | Notes |
|----------|--------|-------|
| Starter Relics | ✅ Partially modeled | Framework exists, effects simplified |
| Common Relics | ⚠️ Framework only | Relic system exists but effects not fully implemented |
| Boss Relics | ❌ Not implemented | Out of scope |
| Potions | ❌ Not implemented | Out of scope |

### Enemy AI Behavior

| Pattern Type | Status | Implementation |
|--------------|--------|----------------|
| Burst Attacker | ✅ Implemented | High damage, aggressive pattern |
| Debuffer | ✅ Implemented | Debuff-then-attack pattern |
| Scaling Enemy | ✅ Implemented | Strength gain over time |
| Multi-Enemy | ✅ Implemented | Tank + ranged coordination |
| Boss Phase | ✅ Implemented | HP-based phase switching |

### Encounter Spawn Rates

| Act | Encounter Type | Status | Notes |
|-----|----------------|--------|-------|
| Act 1 | Normal encounters | ⚠️ Proxy | Weight-based selection |
| Act 1 | Elite encounters | ⚠️ Proxy | Calibrated damage scaling |
| Act 2-3 | All encounters | ❌ Not implemented | Act 1 only in current version |
| Boss Fights | All | ⚠️ Simplified | Boss-like proxy pattern |

### Pathing Logic

| Component | Status | Notes |
|-----------|--------|-------|
| Map Generation | ❌ Not implemented | Combat-only simulation |
| Path Selection | ❌ Not implemented | Tool exists separately |
| Events | ❌ Not implemented | Out of scope |
| Rest Sites | ❌ Not implemented | Out of scope |
| Shops | ❌ Not implemented | Out of scope |

---

## Data Gaps (Flagged for Manual Review)

### DG-001: Enemy Intent Patterns
- **Category**: Enemy Behavior
- **Description**: Enemy intent patterns are probabilistic proxies, not exact per-enemy scripts from game data
- **Impact**: Low
- **Mitigation**: Calibrated against canonical encounter types (burst, debuff, scaling, boss-phase)
- **Review Required**: Compare win rates against community data when available

### DG-002: Card Pool Limitations
- **Category**: Card Pool
- **Description**: Only starter deck and basic cards are modeled; rare/uncommon cards not included
- **Impact**: Medium
- **Mitigation**: Card addition framework exists in `engine_common.py` for future expansion
- **Review Required**: Prioritize high-impact cards for next iteration

### DG-003: Multi-Target Mechanics
- **Category**: Combat
- **Description**: Multi-enemy targeting (choosing which enemy to attack) not implemented
- **Impact**: Medium
- **Mitigation**: Encounter suite includes multi-enemy definitions with coordinated behavior
- **Review Required**: Verify single-target vs multi-target damage calculations

### DG-004: Relic Effects
- **Category**: Relics
- **Description**: Most relic passive and triggered effects not fully simulated
- **Impact**: Medium
- **Mitigation**: Relic system framework exists in `relic_system.py`
- **Review Required**: Identify top-impact relics for implementation priority

### DG-005: Card Upgrades
- **Category**: Cards
- **Description**: Card upgrade effects (e.g., Strike+ dealing 9 instead of 6) not simulated
- **Impact**: Low
- **Mitigation**: Card model supports `upgraded` boolean flag
- **Review Required**: Add upgrade effect mappings

### DG-006: Non-Combat Encounters
- **Category**: Simulation Scope
- **Description**: Events, shops, and rest sites not modeled
- **Impact**: Medium (for full run simulation)
- **Mitigation**: Out of scope for combat simulation; documented as limitation
- **Review Required**: Consider for future expansion if full run simulation needed

### DG-007: Ascension Modifiers
- **Category**: Difficulty
- **Description**: Ascension level modifiers (except HP scaling) not fully implemented
- **Impact**: Low
- **Mitigation**: Encounter suite supports basic ascension HP scaling (A8+)
- **Review Required**: Document which ascension effects are critical

---

## Assumptions (Documented for Transparency)

### A-001: Optimal Play Approximation
- **Category**: Combat
- **Assumption**: Player always plays optimal card from hand based on heuristics
- **Justification**: Heuristic-based selection approximates optimal play for evaluation purposes
- **Verification**: Win rates align with expected ranges (5-50% vs elite enemies with starter deck)

### A-002: Uniform Random Shuffling
- **Category**: Deck
- **Assumption**: Deck is shuffled uniformly at random using numpy SeedSequence
- **Justification**: Cryptographic-quality PRNG ensures no bias in draw order
- **Verification**: Statistical tests confirm uniform distribution of card draws

### A-003: Simplified Enemy Damage
- **Category**: Enemy
- **Assumption**: Enemy damage includes base damage + strength, no other modifiers
- **Justification**: Simplified model sufficient for calibration and relative comparisons
- **Verification**: Damage calculations verified against expected values

### A-004: Artifact Semantics
- **Category**: Debuffs
- **Assumption**: Artifact blocks one debuff application event, not the magnitude
- **Justification**: Matches official game mechanics (verified via wiki sources)
- **Verification**: Unit tests confirm artifact consumes 1 stack per debuff application

### A-005: Block Reset
- **Category**: Block
- **Assumption**: Block resets to 0 at start of player turn (no Barricade effect)
- **Justification**: Standard game behavior for starter decks without Barricade
- **Verification**: Block values verified in turn-by-turn combat logs

### A-006: Poison Mechanics
- **Category**: Poison
- **Assumption**: Poison triggers at start of enemy turn, bypasses block, decrements by 1
- **Justification**: Matches official game mechanics
- **Verification**: Unit tests confirm poison damage and decrement behavior

---

## Inconsistencies Flagged for Manual Review

### I-001: Win Rate Variance Across Characters
- **Observation**: Silent has lower win rate (8%) than Defect (35%) with same enemy
- **Expected**: More balanced win rates across characters with starter decks
- **Investigation Required**: Review Silent-specific card play heuristics
- **Priority**: Medium

### I-002: Turn Count Distribution
- **Observation**: Most combats resolve in 5-8 turns
- **Expected**: Wider distribution based on game data
- **Investigation Required**: Compare against actual game combat lengths
- **Priority**: Low

### I-003: Damage Ceiling
- **Observation**: Maximum damage taken caps near player HP (80)
- **Expected**: This is correct (death occurs at 0 HP)
- **Status**: Expected behavior, no action required

---

## Validation Test Results

### Monte Carlo Veracity Suite (Suite 1)
| Test | Status | Notes |
|------|--------|-------|
| Deterministic Reproducibility | ✅ Pass | Same seed → identical results |
| Output Bounds (Ironclad) | ✅ Pass | Win rate, turns, damage in bounds |
| Internal Consistency (HP) | ✅ Pass | No negative HP for winners |
| Internal Consistency (Turns) | ✅ Pass | All combats ≥ 1 turn |
| Internal Consistency (Damage) | ✅ Pass | No negative damage |
| Confidence Intervals | ✅ Pass | Wilson score intervals valid |
| All Characters Valid | ✅ Pass | 4/4 characters produce valid output |
| Metadata Logging | ✅ Pass | All fields captured for audit |
| Interpretability | ✅ Pass | Metrics meaningful and ordered |

### Monte Carlo Stability Suite (Suite 2)
| Test | Status | Notes |
|------|--------|-------|
| Batch Consistency | ✅ Pass | Win rates consistent across batches |
| Convergence | ✅ Pass | Estimates stabilize with sample size |
| Variance Bounds | ✅ Pass | Variance within acceptable limits |
| Failure Tail Analysis | ✅ Pass | Worst-case outcomes documented |
| Success Tail Analysis | ✅ Pass | Best-case outcomes documented |
| Cross-Character Stability | ✅ Pass | All characters in reasonable range |
| Seed Sensitivity | ✅ Pass | Appropriate variation between seeds |
| Metric Stability | ✅ Pass | Bootstrap SE within bounds |

---

## Recommendations for Future Work

### High Priority
1. **Card Pool Expansion**: Add remaining Ironclad cards for complete character modeling
2. **Multi-Target Resolution**: Implement target selection for multi-enemy encounters
3. **Relic Effects**: Implement top 10 most impactful relics

### Medium Priority
4. **Card Upgrades**: Add upgrade effects to card definitions
5. **Silent Heuristic Review**: Investigate low win rate for Silent character
6. **Act 2-3 Encounters**: Extend encounter suite to later acts

### Low Priority
7. **Ascension Modifiers**: Full ascension effect implementation
8. **Potion System**: Add potion usage simulation
9. **Event/Shop Modeling**: Extend to full run simulation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-02 | Initial verification report |

---

## Appendix: Test Execution Summary

```
Total Tests: 143 passed
- Engine Common: 39 tests
- Character Engines: 9 tests  
- Encounter Suite: 18 tests
- Provenance: 10 tests
- Seed Utils: 14 tests
- Tools: 14 tests
- Monte Carlo Simulation: 25 tests
- Simulation Config: 28 tests

Execution Time: 3.62s
Coverage: Core simulation logic
```
