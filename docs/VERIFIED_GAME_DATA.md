# Slay the Spire - Verified Game Data Reference

**Document Purpose**: This document serves as the canonical, verified source for Slay the Spire game mechanics and data within this repository. All values have been cross-referenced with the official Slay the Spire Wiki and community sources.

**Last Verified**: 2026-02-02

**Sources**:
- [Slay the Spire Wiki (Fandom)](https://slay-the-spire.fandom.com/)
- [SlayTheSpire.gg](https://www.slaythespire.gg/)
- [SlayTheSpire.info](https://slaythespire.info/)
- Official game client (v2.3+)

---

## Character Starting Stats (Verified)

| Character | Starting HP | Starting Energy | Starter Relic |
|-----------|-------------|-----------------|---------------|
| **Ironclad** | 80 | 3 | Burning Blood |
| **Silent** | 70 | 3 | Ring of the Snake |
| **Defect** | 75 | 3 | Cracked Core |
| **Watcher** | 72 | 3 | Pure Water |

### Starter Relic Effects (Verified)

| Relic | Character | Effect |
|-------|-----------|--------|
| **Burning Blood** | Ironclad | At the end of combat, heal 6 HP |
| **Ring of the Snake** | Silent | At the start of each combat, draw 2 additional cards (7 total first turn) |
| **Cracked Core** | Defect | At the start of each combat, Channel 1 Lightning |
| **Pure Water** | Watcher | At the start of each combat, add a Miracle to your hand |

---

## Starter Deck Compositions (Verified)

### Ironclad (10 cards)
| Card | Count | Cost | Type | Effect |
|------|-------|------|------|--------|
| Strike | 5 | 1 | Attack | Deal 6 damage |
| Defend | 4 | 1 | Skill | Gain 5 Block |
| Bash | 1 | 2 | Attack | Deal 8 damage, Apply 2 Vulnerable |

### Silent (12 cards)
| Card | Count | Cost | Type | Effect |
|------|-------|------|------|--------|
| Strike | 5 | 1 | Attack | Deal 6 damage |
| Defend | 5 | 1 | Skill | Gain 5 Block |
| Neutralize | 1 | 0 | Attack | Deal 3 damage, Apply 1 Weak |
| Survivor | 1 | 1 | Skill | Gain 8 Block, Discard 1 card |

### Defect (10 cards)
| Card | Count | Cost | Type | Effect |
|------|-------|------|------|--------|
| Strike | 4 | 1 | Attack | Deal 6 damage |
| Defend | 4 | 1 | Skill | Gain 5 Block |
| Zap | 1 | 1 | Skill | Channel 1 Lightning |
| Dualcast | 1 | 1 | Skill | Evoke your next Orb twice |

**Note**: Defect starts with 3 orb slots.

### Watcher (10 cards)
| Card | Count | Cost | Type | Effect |
|------|-------|------|------|--------|
| Strike | 4 | 1 | Attack | Deal 6 damage |
| Defend | 4 | 1 | Skill | Gain 5 Block |
| Eruption | 1 | 2 | Attack | Deal 9 damage, Enter Wrath |
| Vigilance | 1 | 2 | Skill | Gain 8 Block, Enter Calm |

---

## Damage Calculation (Verified)

### Order of Operations
1. Base damage value from card
2. Add/subtract Strength modifiers
3. Apply Weak (if attacker has it): multiply by 0.75
4. Apply Vulnerable (if defender has it): multiply by 1.5
5. Round down at each step
6. Subtract Block from final damage
7. Remaining damage reduces HP

### Key Formulas

**Attack Damage**:
```
total_damage = floor((base_damage + strength) * weak_multiplier * vulnerable_multiplier)
hp_loss = max(0, total_damage - block)
```

**Block Gain**:
```
total_block = floor((base_block + dexterity) * frail_multiplier)
```

### Multipliers (Verified)

| Status | Effect | Multiplier | Can Be Modified By |
|--------|--------|------------|-------------------|
| **Vulnerable** | Take more Attack damage | 1.5x (50% more) | Paper Phrog relic (1.75x) |
| **Weak** | Deal less Attack damage | 0.75x (25% less) | Paper Krane relic (0.6x / 40% less) |
| **Frail** | Gain less Block | 0.75x (25% less) | - |

**Important**: Weak and Vulnerable only affect Attack-type damage. They do NOT affect:
- Poison damage
- Thorns damage
- Orb damage
- Any non-Attack card damage

---

## Poison Mechanic (Verified - CORRECTED)

**IMPORTANT CORRECTION**: Poison damage occurs at the **START of the poisoned creature's turn**, NOT at the end.

### Poison Tick Sequence
1. **Start of poisoned creature's turn**
2. Creature takes HP damage equal to current Poison stacks
3. Poison bypasses Block completely
4. Poison stacks decrease by 1
5. Creature takes its normal actions

### Example
Enemy has 5 Poison at start of its turn:
- Takes 5 damage
- Poison reduces to 4
- Enemy then performs its attack/action

### Poison vs Artifact
- Artifact blocks the **application** of Poison
- Artifact does NOT block damage from existing Poison
- Each Artifact stack blocks one Poison application event

---

## Artifact Mechanic (Verified)

### Behavior
- Each stack of Artifact negates ONE debuff application
- Consumes 1 stack per debuff, regardless of magnitude
- Applied in order debuffs are listed on cards

### What Artifact Blocks
- Weak
- Vulnerable
- Frail
- Poison (application only)
- Strength loss
- Dexterity loss
- Focus loss (e.g., from Biased Cognition)

### What Artifact Does NOT Block
- Blasphemy's "Die next turn" (classified as a buff)
- Status cards being added to deck
- Curse cards being added to deck
- Direct HP loss

### Multi-Debuff Example
Card applies Weak and Vulnerable with 1 Artifact:
- Artifact blocks Weak (first listed)
- Vulnerable is applied
- Artifact stack is consumed

---

## Orb Mechanics - Defect (Verified - CORRECTED)

### Orb Values (Base + Focus)

| Orb Type | Passive Effect | Passive Value | Evoke Effect | Evoke Value |
|----------|----------------|---------------|--------------|-------------|
| **Lightning** | Deal damage to random enemy | 3 + Focus | Deal damage to random enemy | 8 + Focus |
| **Frost** | Gain Block | 2 + Focus | Gain Block | 5 + Focus |
| **Dark** | Gain stored damage | 6 + Focus | Deal stored damage to lowest HP enemy | All stored |
| **Plasma** | Gain Energy (start of turn) | 1 (NOT affected by Focus) | Gain Energy | 2 (NOT affected by Focus) |

### Key Clarifications

**Plasma Orbs**: Focus does NOT affect Plasma orbs. They always provide:
- Passive: 1 Energy at start of turn
- Evoke: 2 Energy immediately

**Dark Orb Charging**: Focus affects the amount charged per turn, but NOT retroactively. Stored damage is only affected by Focus when being charged.

**Minimum Values**: Orb effects cannot go below 0 even with negative Focus.

### Orb Slot Management
- Default orb slots: 3
- Channeling when full: Evokes leftmost orb first
- Passive trigger order: Right to left at end of turn

---

## Stance Mechanics - Watcher (Verified)

| Stance | Damage Dealt | Damage Received | On Exit | On Enter |
|--------|--------------|-----------------|---------|----------|
| **Neutral** | 1x | 1x | None | None |
| **Wrath** | 2x | 2x | None | None |
| **Calm** | 1x | 1x | Gain 2 Energy | None |
| **Divinity** | 3x | 1x | Auto-exits at start of next turn | Gain 3 Energy |

### Mantra Mechanic
- Accumulates from various cards
- At 10+ Mantra: Enter Divinity, lose 10 Mantra
- Excess Mantra carries over

---

## Act 1 Elite HP Values (Verified)

| Elite | Base HP Range | Ascension 8+ HP |
|-------|---------------|-----------------|
| **Gremlin Nob** | 82-86 | 85-90 |
| **Lagavulin** | 108-112 | 112 |
| **Sentries** (each) | 40-44 | 44 |

### Gremlin Nob Special
- Gains 2 Strength whenever player plays a Skill card
- First turn: Uses Bellow (gains 2 Strength)

### Lagavulin Special
- Starts asleep with 8 Metallicize
- Wakes after 3 turns OR taking damage
- Uses Siphon Soul: -1 Strength, -1 Dexterity

### Sentries Special
- 3 sentries that alternate attacks/daze generation
- Daze: Unplayable status card, Ethereal

---

## Act 1 Boss HP Values (Verified)

| Boss | Base HP | Ascension 9+ HP | Special Mechanic |
|------|---------|-----------------|------------------|
| **Slime Boss** | 140 | 150 | Splits at 50% HP into two 65 HP slimes |
| **The Guardian** | 240 | 250 | Mode Shift between offensive/defensive |
| **Hexaghost** | 250 | 264 | 6-phase attack pattern |

---

## Block Mechanics (Verified)

### Standard Behavior
- Block resets to 0 at start of player's turn
- Block absorbs damage before HP
- Block cannot go negative
- Maximum Block: 999

### Block Retention
Cards/relics that modify block retention:
- **Barricade** (Power): Block never expires
- **Blur** (Skill): Block retained for one extra turn
- **Calipers** (Relic): Lose 15 Block per turn instead of all

---

## Status Cards (Verified)

| Status Card | Effect | Properties |
|-------------|--------|------------|
| **Dazed** | Unplayable | Ethereal |
| **Wound** | Unplayable | - |
| **Burn** | Unplayable, take 2 damage if in hand at end of turn | - |
| **Burn+** | Unplayable, take 4 damage if in hand at end of turn | - |
| **Slimed** | Costs 1, Exhaust | - |
| **Void** | Unplayable, Ethereal, lose 1 Energy when drawn | - |

---

## Verification Changelog

### 2026-02-02
- Verified all character starting HP values
- Corrected Poison timing (start of turn, not end)
- Verified Defect starter deck (10 cards, not 12)
- Confirmed Plasma orbs are NOT affected by Focus
- Verified elite and boss HP ranges
- Confirmed Artifact behavior with multi-debuff cards
- Verified starter relic exact effects

---

## References

1. Slay the Spire Wiki - Block: https://slay-the-spire.fandom.com/wiki/Block
2. Slay the Spire Wiki - Poison: https://slay-the-spire.fandom.com/wiki/Poison
3. Slay the Spire Wiki - Artifact: https://slay-the-spire.fandom.com/wiki/Artifact
4. Slay the Spire Wiki - Orbs: https://slay-the-spire.fandom.com/wiki/Orbs
5. Slay the Spire Wiki - Gremlin Nob: https://slay-the-spire.fandom.com/wiki/Gremlin_Nob
6. Slay the Spire Wiki - Vulnerable: https://slay-the-spire.fandom.com/wiki/Vulnerable
7. Slay the Spire Wiki - Weak: https://slay-the-spire.fandom.com/wiki/Weak
8. SlayTheSpire.gg - All Elites: https://www.slaythespire.gg/elites
9. SlayTheSpire.gg - All Bosses: https://www.slaythespire.gg/bosses
