# Slay the Spire - Game Mechanics Reference

This document provides a comprehensive reference for Slay the Spire game mechanics as implemented in the simulation framework. It serves as the canonical source for game rules within this repository.

---

## Table of Contents

1. [Core Mechanics](#core-mechanics)
2. [Combat Flow](#combat-flow)
3. [Cards](#cards)
4. [Keywords](#keywords)
5. [Debuffs and Buffs](#debuffs-and-buffs)
6. [Characters](#characters)
7. [Enemies](#enemies)
8. [Relics](#relics)

---

## Core Mechanics

### Health (HP)

- **Max HP**: The maximum health a character can have
- **Current HP**: Damage reduces this; death occurs at 0
- **Healing**: Cannot exceed Max HP

### Energy

- **Default**: 3 energy per turn for all characters
- **Refresh**: Energy resets at start of each turn (unused is lost)
- **Cost**: Cards require energy to play

### Block

- **Function**: Absorbs incoming damage before HP
- **Duration**: Expires at start of player's next turn
- **Stacking**: Multiple block sources add together
- **Calculation**: `damage_to_hp = max(0, attack_damage - block)`

### Deck System

```
[Draw Pile] ──draw──> [Hand] ──play──> [Discard Pile]
                        │                    │
                        └───discard──────────┘
                                             │
                           reshuffle when draw pile empty
                                             │
                        ┌────────────────────┘
                        v
                   [Draw Pile]
                   
[Exhaust Pile] ◄── exhaust ── [Hand]  (removed from combat)
```

- **Hand Size**: Default 5 cards drawn per turn
- **Hand Limit**: 10 cards maximum
- **Reshuffle**: When draw pile empty, shuffle discard into draw pile

---

## Combat Flow

### Turn Order

1. **Start of Player Turn**
   - Block resets to 0
   - Energy refreshes to max
   - Draw 5 cards (or modified amount)
   - Trigger start-of-turn effects

2. **Player Action Phase**
   - Play cards from hand
   - Use potions
   - Cards resolved immediately
   - Repeat until no energy or done

3. **End of Player Turn**
   - Discard remaining hand
   - Trigger end-of-turn effects

4. **Enemy Turn**
   - Execute enemy intent
   - Process poison damage (end of enemy turn)
   - Decrement debuffs
   - Select new intent

### Intent System

Enemies telegraph their next action:
- **Attack** (sword icon): Will deal damage
- **Defend** (shield icon): Will gain block
- **Buff** (up arrow): Will strengthen self
- **Debuff** (down arrow): Will apply debuffs to player
- **Unknown** (?): Intent is hidden

---

## Cards

### Card Types

| Type | Description |
|------|-------------|
| **Attack** | Deals damage (red/green card back in-game) |
| **Skill** | Non-damage effects (blue card back) |
| **Power** | Permanent effects for combat duration |
| **Status** | Negative cards added to deck (unplayable) |
| **Curse** | Negative cards with harmful effects |

### Card Properties

- **Cost**: Energy required to play (0-5, or X)
- **Upgraded**: Enhanced version with better effects
- **Innate**: Drawn in opening hand
- **Ethereal**: Exhausts if not played by end of turn
- **Exhaust**: Removed from deck for remainder of combat
- **Retain**: Kept in hand instead of discarding

### Damage Calculation

```
Base Damage → +Strength → ×Vulnerability → -Block → HP Loss

Formula:
1. total_damage = base_damage + player.strength
2. if enemy.vulnerable > 0:
      total_damage = floor(total_damage × 1.5)
3. if enemy.block >= total_damage:
      enemy.block -= total_damage
      hp_loss = 0
   else:
      hp_loss = total_damage - enemy.block
      enemy.block = 0
      enemy.hp -= hp_loss
```

### Block Calculation

```
Base Block → +Dexterity → Applied to Player

Formula:
1. total_block = base_block + player.dexterity
2. player.block += total_block
```

---

## Keywords

### Vulnerability

- **Effect**: Target takes 50% more damage from attacks
- **Formula**: `damage = floor(base_damage × 1.5)`
- **Duration**: Decrements by 1 at end of turn
- **Blocked by**: Artifact

### Weakness

- **Effect**: Target deals 25% less damage from attacks
- **Formula**: `damage = floor(base_damage × 0.75)`
- **Duration**: Decrements by 1 at end of turn
- **Blocked by**: Artifact

### Artifact

- **Effect**: Blocks one debuff application
- **Behavior**: Consumes one stack per debuff EVENT (not magnitude)
- **Example**: Artifact blocks applying 5 Vulnerable; the 5 stacks are blocked as one event

### Poison

- **Effect**: At **START of poisoned creature's turn**, takes poison damage and poison decreases by 1
- **Formula**: 
  - `enemy.hp -= enemy.poison` (damage bypasses Block)
  - `enemy.poison -= 1`
- **Timing**: START of turn, BEFORE enemy takes action
- **Blocked by**: Artifact (blocks application, not existing poison)
- **Important**: Poison bypasses Block completely

### Strength

- **Effect**: Increases attack damage
- **Formula**: `damage = base_damage + strength`
- **Stacking**: Additive
- **Duration**: Permanent (unless explicitly reduced)

### Dexterity

- **Effect**: Increases block gain
- **Formula**: `block = base_block + dexterity`
- **Stacking**: Additive
- **Duration**: Permanent (unless explicitly reduced)

### Intangible

- **Effect**: Reduces all HP loss to 1
- **Duration**: Until end of turn
- **Exception**: Does not prevent 999+ damage (Heart fight)

### Focus (Defect)

- **Effect**: Increases orb passive and evoke values
- **Formula**: `orb_value = base_value + focus`
- **Minimum**: Orb values cannot go below 0

### Mantra (Watcher)

- **Effect**: At 10 mantra, enter Divinity stance
- **Accumulation**: Additive
- **Trigger**: Automatically enters Divinity at 10+

---

## Debuffs and Buffs

### Player Debuffs

| Debuff | Effect |
|--------|--------|
| Weak | Deal 25% less damage |
| Frail | Gain 25% less block |
| Vulnerable | Take 50% more damage |
| Entangled | Cannot play attacks this turn |
| No Draw | Cannot draw cards next turn |

### Enemy Debuffs

| Debuff | Effect |
|--------|--------|
| Weak | Deal 25% less damage |
| Vulnerable | Take 50% more damage |
| Poison | Take damage and decrement at end of turn |

### Player Buffs

| Buff | Effect |
|------|--------|
| Strength | +1 damage per attack per stack |
| Dexterity | +1 block per block card per stack |
| Artifact | Block 1 debuff application per stack |
| Metallicize | Gain block at end of turn |
| Plated Armor | Gain block at end of turn; removed if HP lost |

---

## Characters

### The Ironclad

**Theme**: Strength scaling, self-damage, healing

| Stat | Value |
|------|-------|
| Starting HP | 80 |
| Starting Energy | 3 |
| Starting Relic | Burning Blood (+6 HP after combat) |

**Starter Deck (10 cards)**:
- 5× Strike (1 energy, 6 damage)
- 4× Defend (1 energy, 5 block)
- 1× Bash (2 energy, 8 damage, 2 Vulnerable)

**Key Mechanics**:
- Strength stacking (Inflame, Limit Break)
- Multi-hit attacks with strength (Heavy Blade)
- Self-damage for power (Brutality, Hemokinesis)
- Exhaust synergies (Feel No Pain)

### The Silent

**Theme**: Poison, discard synergies, shivs

| Stat | Value |
|------|-------|
| Starting HP | 70 |
| Starting Energy | 3 |
| Starting Relic | Ring of the Snake (+2 cards turn 1) |

**Starter Deck (12 cards)**:
- 5× Strike (1 energy, 6 damage)
- 5× Defend (1 energy, 5 block)
- 1× Survivor (1 energy, 8 block, discard 1)
- 1× Neutralize (0 energy, 3 damage, 1 Weak)

**Key Mechanics**:
- Poison stacking (Deadly Poison, Catalyst)
- Shiv generation (Blade Dance, Infinite Blades)
- Discard synergies (Tactician, Reflex)
- Weak application for defense

### The Defect

**Theme**: Orbs, focus scaling, multi-hit

| Stat | Value |
|------|-------|
| Starting HP | 75 |
| Starting Energy | 3 |
| Starting Relic | Cracked Core (channel 1 Lightning at start) |
| Starting Orb Slots | 3 |

**Starter Deck (12 cards)**:
- 4× Strike (1 energy, 6 damage)
- 4× Defend (1 energy, 5 block)
- 1× Zap (1 energy, channel Lightning)
- 1× Dualcast (1 energy, evoke rightmost orb twice)

**Orb Types**:

| Orb | Passive (per turn) | Evoke |
|-----|-------------------|-------|
| Lightning | 3+focus damage to random enemy | 8+focus damage |
| Frost | 2+focus block | 5+focus block |
| Dark | Gain 6+focus dark power | Deal accumulated |
| Plasma | 1 energy/turn (NOT focus) | Gain 2 energy (NOT focus) |

**Note**: Plasma orbs are NOT affected by Focus. Their values are always fixed.

**Key Mechanics**:
- Orb cycling (channel/evoke)
- Focus stacking (Defragment, Consume)
- Orb slot management (Capacitor)
- Multi-orb synergies (Electrodynamics)

### The Watcher

**Theme**: Stances, mantra, scrying

| Stat | Value |
|------|-------|
| Starting HP | 72 |
| Starting Energy | 3 |
| Starting Relic | Pure Water (add Miracle to hand turn 1) |

**Starter Deck (10 cards)**:
- 4× Strike (1 energy, 6 damage)
- 4× Defend (1 energy, 5 block)
- 1× Eruption (2 energy, 9 damage, enter Wrath)
- 1× Vigilance (2 energy, 8 block, enter Calm)

**Stances**:

| Stance | Effect |
|--------|--------|
| Neutral | No modifiers |
| Wrath | Deal and receive 2× damage |
| Calm | Gain 2 energy when exiting |
| Divinity | Deal 3× damage, +3 energy, auto-exits |

**Key Mechanics**:
- Stance dancing (enter/exit for bonuses)
- Mantra accumulation (10 = Divinity)
- Retain cards (keep across turns)
- Scry (view and discard from draw pile)

---

## Enemies

### Enemy AI Patterns

Enemies follow semi-deterministic patterns:

```python
# Simplified pattern (actual patterns vary by enemy)
if turn == 1:
    return ATTACK
elif random() < 0.5:
    return ATTACK
elif random() < 0.3:
    return BUFF
else:
    return DEFEND
```

### Common Enemy Types

**Act 1 Enemies**:
- Cultist: Incremental attack buff
- Jaw Worm: Attack/defend/buff cycle
- Louse: Random attack strength

**Act 1 Elites**:
- Gremlin Nob (82 HP): Gains strength when skills played
- Lagavulin (112 HP): Debuffs player each turn
- Sentries (38 HP each): Constant daze generation

**Bosses** (not yet implemented):
- Slime Boss, Hexaghost, The Guardian

### Enemy Intent Values

| Intent | Icon | Meaning |
|--------|------|---------|
| Attack | Sword | Damage amount shown |
| Defend | Shield | Block amount (hidden) |
| Buff | Up Arrow | Self-buff coming |
| Debuff | Down Arrow | Player debuff coming |
| Unknown | ? | Multi-action or hidden |

---

## Relics

### Starter Relics

| Character | Relic | Effect |
|-----------|-------|--------|
| Ironclad | Burning Blood | Heal 6 HP at end of combat |
| Silent | Ring of the Snake | Draw 2 additional cards turn 1 |
| Defect | Cracked Core | Channel 1 Lightning at start |
| Watcher | Pure Water | Add Miracle to hand turn 1 |

### Common Relics (Examples)

| Relic | Effect |
|-------|--------|
| Bag of Preparation | Draw 2 additional cards turn 1 |
| Blood Vial | Heal 2 HP at start of combat |
| Anchor | Start combat with 10 Block |
| Vajra | Start combat with +1 Strength |
| Lantern | Gain 1 energy turn 1 |

### Boss Relics (Examples)

| Relic | Effect |
|-------|--------|
| Snecko Eye | +2 energy, Confused |
| Runic Dome | +1 energy, can't see intents |
| Coffee Dripper | +1 energy, can't rest |
| Velvet Choker | +1 energy, 6 card limit |
| Sozu | +1 energy, can't use potions |

---

## References

This documentation is based on:
- [Slay the Spire Wiki](https://slay-the-spire.fandom.com/wiki/Slay_the_Spire_Wiki)
- [Spirelogs Community Data](https://spirelogs.com/)
- In-game tooltips and mechanics testing

For the most authoritative game mechanics, refer to the actual game client.
