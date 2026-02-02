# Task: Slay the Spire Monte Carlo Simulation & Documentation Package

## Role
Act as a technical writer with expertise in probabilistic modelling and game theory.

## Objective
Produce a scholarly-grade **Companion Data Pack** (PDF, DOCX, XLSX) for a Slay the Spire Monte Carlo simulation system.

---

## Phase 1: Simulation Validation (Complete First)

Run **2 large-batch tests** (10,000 iterations each) across these scenarios:
- **Base** — deterministic, no heuristics
- **Complex** — synergy-driven decision trees
- **Ideal** — perfect-play oracle
- **Random** — robustness stress-test

**Metrics to capture:**
- Win rate, median turn count, variance, 5% tail-risk

**Data verification checklist:**
- [ ] Card mechanics (all characters, colourless, curses, status effects)
- [ ] Relic interactions
- [ ] Potion effects
- [ ] Enemy AI patterns and spawn rates
- [ ] Boss behaviours

Cross-reference against SpireSpy, Tiny Helper, and STSDeckAssistant for accuracy.

---

## Phase 2: Document Generation (After Phase 1)

### Structure
Use the Deck Evaluation Framework:
$$\text{Score} = 0.4Q + 0.25S + 0.15C + 0.10K + 0.10R$$

### Content Approach
**Hybrid**: Include full SpireSpy data integrated with simulation results. Fill gaps using verified community sources.

### Deliverables
1. **PDF** — Print-quality, peer-review-ready report
2. **DOCX** — Editable version with methodology notes
3. **XLSX** — Raw data, formulas, `Deck_Eval_Model` sheet

---

## Constraints
- Use deterministic PRNG seeds (20260202, 31415926) for reproducibility
- Flag any SpireSpy data discrepancies for manual review
- No game file modification—observational data only
- Proofread all outputs before delivery

---

## Confirmation
This is a **final content request**. Proceed through both phases and deliver completed files with download links.