# AI/ML Research in Slay the Spire

## Executive Summary

This document surveys academic and practical research on artificial intelligence and machine learning applications to Slay the Spire. The game serves as an excellent testbed for AI research due to its combination of strategic depth, stochastic elements, and complex decision spaces.

---

## Table of Contents

1. [Research Overview](#research-overview)
2. [Neural Network Applications](#neural-network-applications)
3. [Reinforcement Learning](#reinforcement-learning)
4. [Entropy and Risk Analysis](#entropy-and-risk-analysis)
5. [Luck vs. Skill Quantification](#luck-vs-skill-quantification)
6. [Optimization and Search](#optimization-and-search)
7. [Quantum-Inspired Approaches](#quantum-inspired-approaches)
8. [Future Directions](#future-directions)
9. [References](#references)

---

## Research Overview

### Why Slay the Spire for AI Research?

Slay the Spire presents several characteristics that make it valuable for AI/ML research:

| Characteristic | Research Value |
|----------------|----------------|
| **Large State Space** | Cards, relics, HP, enemies create ~10^50+ states |
| **Stochastic Outcomes** | Card draws, encounters, rewards provide uncertainty |
| **Long-Term Planning** | Decisions in Act 1 affect Act 3 viability |
| **Incomplete Information** | Future encounters unknown until revealed |
| **High Skill Ceiling** | Top players achieve 70-90% win rates; AI benchmark |
| **Accessibility** | Active modding community, available on multiple platforms |

### Research Themes

1. **Pathfinding**: Optimal map navigation through procedural acts
2. **Deck Construction**: Card selection and synergy discovery
3. **Combat Strategy**: Turn-by-turn card play optimization
4. **Risk Management**: Balancing HP, gold, and power progression
5. **Meta-Learning**: Adapting strategies across different runs

---

## Neural Network Applications

### Path Prediction with ANNs

**Research**: Malmö University (2021)  
**Authors**: Student thesis project  
**Method**: Artificial Neural Networks trained on player gameplay data

#### Methodology

- **Dataset**: Thousands of player runs with win/loss outcomes
- **Features**: Map paths taken, elite counts, campfire usage, HP management
- **Target**: Predict optimal path choices at each node
- **Architecture**: Feedforward neural networks with multiple hidden layers

#### Key Findings

1. **Elite Fights Correlate with Success**
   - Paths with more elite encounters have higher win rates
   - Despite HP risk, relics from elites are critical for scaling

2. **Campfire Timing Matters**
   - Strategic use of campfires for upgrades vs. healing
   - Top players upgrade more frequently early, heal more strategically later

3. **Node Type Preferences**
   - Elite > Campfire > Shop > Event > Normal Combat (in terms of long-term value)
   - Event variance is high; risk-averse paths avoid too many unknowns

4. **Path Length**
   - Longer paths (more nodes) generally better if HP permits
   - More opportunities for rewards, upgrades, and optimization

#### Limitations

- Model trained on lower-Ascension data; high-Ascension patterns differ
- Does not account for current deck state (treats all paths equally)
- Binary win/loss outcome doesn't capture quality of victory

#### Reference

**Using machine learning to help find paths through the map in Slay the Spire**  
Malmö University Digital Thesis Archive (2021)  
[PDF Link](https://www.diva-portal.org/smash/get/diva2:1565751/FULLTEXT02.pdf)

### Deep Learning for Card Evaluation

**Research**: Various community projects  
**Method**: Neural networks trained to evaluate card strength

#### Approach

- **Input**: Current deck, available relics, character, act, HP
- **Output**: Predicted value of adding each offered card
- **Training**: Supervised learning on expert gameplay or RL-generated data

#### Challenges

- **Context-Dependence**: Card value varies wildly based on deck composition
- **Synergy Detection**: Model must learn interaction effects, not just individual card strength
- **Data Scarcity**: High-quality labeled data (expert choices with outcomes) is limited

#### Results

- Models can learn basic heuristics (e.g., prefer damage in Act 1, scaling later)
- Struggle with complex synergies (e.g., Dead Branch + Corruption)
- Human experts still significantly outperform in nuanced situations

---

## Reinforcement Learning

### Overview

Reinforcement Learning (RL) is a natural fit for Slay the Spire:
- **Agent**: The player/AI making decisions
- **Environment**: The game state (deck, relics, HP, enemies)
- **Actions**: Card plays, card selections, path choices
- **Rewards**: Combat victories, run completion, HP preservation

### Algorithms Applied

#### 1. Proximal Policy Optimization (PPO)

**Advantages**:
- Stable training compared to vanilla policy gradient
- Good for high-dimensional action spaces
- Efficient sample usage

**Application**:
- Combat AI: Which cards to play each turn
- Learns basic strategies (defend when enemy attacks, buff then attack)

**Results**:
- Can defeat Act 1 enemies consistently
- Struggles with complex card interactions and long-term planning

#### 2. Advantage Actor-Critic (A2C)

**Advantages**:
- Faster training than PPO in some cases
- Value function helps credit assignment

**Application**:
- Combined card selection and combat
- Learns to prioritize certain card types based on character

**Results**:
- Similar performance to PPO
- Better at short-term tactics than long-term strategy

#### 3. Deep Q-Networks (DQN)

**Advantages**:
- Off-policy: can learn from any gameplay data
- Replay buffer improves sample efficiency

**Application**:
- Card selection at rewards screen
- Q-values estimate long-term value of adding each card

**Results**:
- Difficult due to large action space (many possible cards)
- Requires heavy action abstraction

### Challenges for RL in STS

#### 1. State Representation

**Problem**: Full game state is extremely high-dimensional

**Solutions**:
- **Hand-crafted features**: Extract key stats (HP, energy, deck size, etc.)
- **Learned embeddings**: Neural networks encode card/relic sets
- **Attention mechanisms**: Weight important cards/relics more heavily

#### 2. Action Space

**Problem**: Hundreds of possible cards; many possible plays per turn

**Solutions**:
- **Action abstraction**: Group similar cards, limit choices
- **Hierarchical RL**: High-level strategy (deck archetype) → Low-level tactics (card plays)
- **Mask invalid actions**: Only consider legal/sensible plays

#### 3. Reward Shaping

**Problem**: Winning/losing is sparse (only at end of run); hard to credit early decisions

**Solutions**:
- **Intermediate rewards**: HP preservation, elite victories, Act completions
- **Potential-based shaping**: Reward progress toward winning conditions
- **Intrinsic motivation**: Reward exploration and novelty

#### 4. Stochasticity

**Problem**: Random card draws, encounters, enemy actions

**Solutions**:
- **Expectation over randomness**: Train on diverse seeds
- **Belief states**: Model uncertainty over future events
- **Robust policies**: Learn strategies that work across many scenarios

### Notable Projects

#### Communication AI

**Developer**: ForgottenArbiter (GitHub)  
**Approach**: Modding framework for external AI control  
**Features**: API for game state access, action execution  
**Status**: Active community use; enables research

#### Various Academic Implementations

**Institutions**: Multiple universities worldwide  
**Courses**: Used in AI/ML courses as final project  
**Typical Results**: Beat Act 1, struggle with Acts 2-3

### Current Best Practices

1. **Start Simple**: Train on single character, low Ascension
2. **Incremental Complexity**: Add mechanics gradually (combat → pathing → full runs)
3. **Use Domain Knowledge**: Incorporate game rules as inductive biases
4. **Hybrid Approaches**: Combine RL with heuristics or search

---

## Entropy and Risk Analysis

### Research: Uncertainty in Procedural Maps

**Publication**: arXiv (2025)  
**Title**: *Analysis of Uncertainty in Procedural Maps in Slay the Spire*  
**Link**: [arXiv:2504.03918v1](https://arxiv.org/html/2504.03918v1)

### Methodology

- **Dataset**: Over 20,000 player runs from community databases
- **Metrics**: Path entropy, node type distribution, outcome (win/loss)
- **Analysis**: Statistical correlation between path characteristics and success

### Key Findings

#### 1. High-Entropy Paths Correlate with Wins

**Entropy Definition**: Measure of unpredictability in path choices

**Results**:
- **Winning players** tend to take higher-entropy paths
- Higher-entropy = more elite fights, more events, less predictable route
- **Losing players** tend to take lower-entropy (safer) paths

**Interpretation**:
- Skilled players embrace calculated risk
- Safe paths yield insufficient power for late-game challenges
- Mastery involves **risk management**, not risk avoidance

#### 2. Event Node Variance

**Finding**: Event nodes have highest outcome variance

**Implications**:
- Events can provide major benefits (relics, card removals) or penalties (curses, HP loss)
- Top players handle variance better through potion management and HP cushion
- Risk-averse players avoid events, limiting upside potential

#### 3. Elite Density

**Finding**: Successful runs average 2-3 elites per act (depending on Ascension)

**Implications**:
- Too few elites = insufficient relics, deck remains weak
- Too many elites = excessive HP loss, high risk of death
- Optimal elite count balances risk and reward

#### 4. Campfire Usage Patterns

**Finding**: Winners upgrade more early, rest more later

**Implications**:
- Early upgrades compound value throughout run
- Late-game HP more precious as challenges intensify
- Strategic planning of campfire usage is critical

### Theoretical Framework

**Risk-Sensitive Decision-Making**:
- Traditional expected value (EV) maximization insufficient
- Need to account for **risk tolerance** and **downside protection**
- Quantum-inspired probability models may better capture this

**Entropy as Skill Indicator**:
- Low entropy = following scripted strategy, not adapting
- High entropy = adaptive, context-dependent decisions
- AI should maximize **informed** entropy, not random choices

---

## Luck vs. Skill Quantification

### Research: Randomness in Slay the Spire

**Publication**: IEEE Conference on Games (CoG) 2023  
**Title**: *Are You Lucky or Skilled? An Analysis of Elements of Randomness in Slay the Spire*  
**Authors**: Andersson et al.  
**Link**: [PDF](https://aeau.github.io/assets/papers/2023/andersson2023-cog03.pdf)

### Research Questions

1. How much does luck vs. skill determine outcomes?
2. Can we quantify the contribution of each?
3. What makes a player "skilled" in STS?

### Methodology

- **Dataset**: Streamer runs, leaderboard data, community gameplay
- **Variables**: Card/relic offerings, path options, combat RNG, player decisions
- **Analysis**: Variance decomposition, regression models, counterfactual simulation

### Key Findings

#### 1. Luck Matters, But...

**Quantification**:
- **Card/relic luck** accounts for ~30-40% of win rate variance
- Getting key cards/relics early dramatically increases win probability
- Some seeds are objectively harder (poor offerings, harsh events)

**But**:
- Top players win even with "unlucky" seeds (50-70% win rate)
- Average players lose even with "lucky" seeds (60-70% loss rate)
- **Skill dominates** in aggregate

#### 2. Skill Manifestations

**What Skilled Players Do Differently**:

1. **Adaptation**: Recognize and pivot to available synergies, don't force archetypes
2. **Risk Calibration**: Take calculated risks (elite fights), avoid unnecessary risks (bad events)
3. **Resource Optimization**: Maximize value from gold, potions, campfires
4. **Probabilistic Thinking**: Play to maximize win probability, not greedy immediate gains
5. **Deck Thinning**: Aggressively remove weak cards

#### 3. Win Rate Distribution

**Observed Win Rates by Skill Level**:

| Player Tier | Ascension 20 Win Rate |
|-------------|----------------------|
| Beginners | 5-15% |
| Intermediate | 20-35% |
| Advanced | 40-60% |
| Expert | 65-80% |
| World-Class | 80-90%+ (in specific conditions) |

**Implications**:
- Massive skill gradient exists
- Even with perfect play, some runs are unwinnable (RNG can dominate)
- But over many runs, skill emerges clearly

#### 4. Decision Points

**Critical Decision Moments** (highest skill expression):

1. **Card Selection**: Choosing which cards to add/skip
2. **Pathing**: Which nodes to visit
3. **Combat**: Which cards to play each turn
4. **Card Removal**: Which cards to remove at shops
5. **Boss Relic**: Which boss relic to take (huge impact)

**Low-Skill Decision Moments**:
- Random event outcomes (limited choice impact)
- Enemy AI (deterministic intent system)

### Implications for AI

1. **Need for Exploration**: AI must explore different strategies to learn adaptation
2. **Importance of Heuristics**: Encode expert knowledge to bootstrap learning
3. **Robust Policies**: AI should perform reasonably even with poor RNG
4. **Meta-Learning**: Learn to learn; adapt quickly to new card/relic combinations

---

## Optimization and Search

### Monte Carlo Tree Search (MCTS)

**Application**: Combat decision-making

**Approach**:
- **Tree**: Each node = game state; edges = possible actions
- **Simulation**: Rollout random plays from current state to end of combat
- **Selection**: Choose action with best expected outcome
- **Expansion**: Grow tree by exploring promising branches

**Challenges**:
- **Branching Factor**: Many possible plays per turn (hand size × play order)
- **Depth**: Combats can last 10+ turns
- **Stochasticity**: Enemy actions, card draws introduce randomness

**Results**:
- Works well for single-combat optimization
- Computational cost high for full-run planning
- Hybrid MCTS + heuristics shows promise

### Genetic Algorithms

**Application**: Deck optimization

**Approach**:
- **Population**: Pool of deck configurations
- **Fitness**: Simulated performance against benchmark encounters
- **Evolution**: Mutate (add/remove cards), crossover (combine decks), select best

**Results**:
- Can discover unexpected synergies
- Requires many simulations (computationally expensive)
- Biased toward decks that beat specific encounters (may not generalize)

### Dynamic Programming

**Application**: Path planning

**Approach**:
- **States**: Nodes on map with associated deck/HP/relic state
- **Value Function**: Expected win probability from each state
- **Backward Induction**: Compute values from boss to start

**Challenges**:
- **State Space Explosion**: Deck configurations are immense
- **Uncertainty**: Future offerings unknown
- **Abstraction**: Must group similar states

**Results**:
- Effective for simplified models (fixed decks, abstracted states)
- Full-fidelity implementation remains intractable

---

## Quantum-Inspired Approaches

### Motivation

Quantum-inspired algorithms can address STS challenges:

1. **Superposition of Strategies**: Maintain multiple possible deck archetypes simultaneously
2. **Interference**: Model synergies and anti-synergies as constructive/destructive interference
3. **Entanglement**: Capture dependencies between cards, relics, and game state
4. **Measurement Effects**: Model how decisions collapse future possibilities

### Quantum Decision Theory for Card Selection

**Approach**:
- Represent player's preference state as quantum superposition
- Each possible card choice = basis state
- Decision "measurement" collapses to selected card
- Context (current deck, relics) affects probability amplitudes

**Advantages**:
- Naturally models context-dependence
- Captures preference reversals (card value changes based on what's seen first)
- Can explain disjunction effects in player decision-making

### Quantum Annealing for Deck Optimization

**Approach**:
- Encode deck configuration as quantum state
- Define energy function (lower energy = better deck)
- Use quantum annealing to find ground state (optimal deck)

**Challenges**:
- Requires quantum hardware (D-Wave, etc.) or simulation
- Energy function design is non-trivial
- Currently theoretical; no implementations published

### Quantum-Inspired Classical Algorithms

**Approach**:
- Use quantum probability without requiring quantum hardware
- Interference models for synergy detection
- Quantum game theory for strategic planning

**Promising Directions**:
1. **Amplitude Amplification**: Boost probability of good card combinations
2. **Quantum Walks**: Explore card/relic space more efficiently
3. **Tensor Networks**: Represent complex card interactions compactly

---

## Future Directions

### 1. Hierarchical RL

**Proposal**: Multi-level learning architecture
- **Level 1**: Strategic (deck archetype, path planning)
- **Level 2**: Tactical (combat card play)
- **Level 3**: Execution (play order optimization)

**Benefits**:
- Decompose complex problem into manageable sub-problems
- Each level learns at appropriate time scale
- Transfer learning across characters/runs

### 2. Meta-Learning / Few-Shot Adaptation

**Proposal**: Learn to adapt quickly to new card/relic combinations

**Approach**:
- Train on diverse runs
- Learn meta-strategies that generalize
- Fine-tune rapidly when encountering new synergies

**Benefits**:
- Mimics expert player adaptability
- Reduces data requirements for new strategies
- Handles novelty better

### 3. Explainable AI

**Proposal**: AI that explains its decisions

**Approach**:
- Attention mechanisms highlight important cards/relics
- Natural language generation describes reasoning
- Counterfactual explanations ("if I had card X instead...")

**Benefits**:
- Helps human players learn
- Builds trust in AI recommendations
- Facilitates debugging and improvement

### 4. Multi-Agent Competition

**Proposal**: Multiple AI agents compete, learn from each other

**Approach**:
- Population-based training
- Agents specialize in different strategies
- Co-evolution drives discovery of novel tactics

**Benefits**:
- Faster exploration of strategy space
- Robust to changes in game balance
- Scalable to multiplayer variants (STS2 co-op?)

### 5. Integration with Quantum Computing

**Proposal**: As quantum hardware matures, implement quantum algorithms

**Target Applications**:
- Portfolio optimization → Deck optimization
- Quantum sampling → Procedural generation analysis
- Quantum ML → Card embedding learning

**Timeline**: 5-10 years until practical quantum advantage likely

---

## References

### Academic Papers

1. **Using machine learning to help find paths through the map in Slay the Spire**  
   Malmö University (2021)  
   [PDF](https://www.diva-portal.org/smash/get/diva2:1565751/FULLTEXT02.pdf)

2. **Analysis of Uncertainty in Procedural Maps in Slay the Spire**  
   arXiv (2025)  
   [arXiv:2504.03918v1](https://arxiv.org/html/2504.03918v1)

3. **Are You Lucky or Skilled? An Analysis of Elements of Randomness in Slay the Spire**  
   IEEE Conference on Games (2023)  
   [PDF](https://aeau.github.io/assets/papers/2023/andersson2023-cog03.pdf)

4. **'Slay the Spire': Metrics Driven Design and Balance**  
   GDC Vault (2019)  
   [GDC Vault](https://www.gdcvault.com/play/1025731/-Slay-the-Spire-Metrics)

### Community Resources

- **Communication AI Mod**: [GitHub - ForgottenArbiter/CommunicationMod](https://github.com/ForgottenArbiter/CommunicationMod)
- **Slay the Spire Wiki**: [Fandom](https://slay-the-spire.fandom.com/)
- **r/slaythespire**: Active research discussion

### Related AI/ML Topics

- **Reinforcement Learning**: Sutton & Barto, *Reinforcement Learning: An Introduction* (2018)
- **Monte Carlo Tree Search**: Browne et al., *A Survey of Monte Carlo Tree Search Methods* (2012)
- **Quantum Machine Learning**: Schuld & Petruccione, *Supervised Learning with Quantum Computers* (2018)

---

## Conclusion

AI/ML research in Slay the Spire demonstrates:

1. **Game is Solvable**: AI can learn competent strategies
2. **Human Expertise Remains Superior**: Top players outperform current AI
3. **Rich Research Platform**: Many open problems remain
4. **Cross-Disciplinary**: Bridges game AI, RL, quantum computing, decision theory

The combination of strategic depth and accessibility makes STS an ideal benchmark for next-generation AI decision-making systems.

---

**Last Updated**: February 2026  
**Status**: Comprehensive AI/ML research survey  
**Next Steps**: Implement prototype decision-support tools based on research findings
