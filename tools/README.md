# Decision-Support Tools for Slay the Spire

This directory contains prototype decision-support tools based on research findings from AI/ML studies and expert strategy analysis.

## Tools

### 1. Synergy Analyzer (`synergy_analyzer.py`)

Analyzes potential synergies between cards and relics to help players make informed deck-building decisions.

**Features:**
- Identifies active synergies in current deck
- Calculates synergy scores based on card/relic combinations
- Provides strategic recommendations
- Suggests best cards to add for synergy improvement

**Usage:**
```python
from synergy_analyzer import SynergyAnalyzer

analyzer = SynergyAnalyzer()

# Analyze a deck
deck = ['Strike', 'Defend', 'Heavy Blade', 'Demon Form', ...]
relics = ['Burning Blood', 'Vajra', 'Girya']
analysis = analyzer.analyze_deck(deck, relics)

# Find best cards to add
available = ['Sword Boomerang', 'Twin Strike', 'Battle Trance']
recommendations = analyzer.find_best_additions(deck, relics, available)
```

**Run Example:**
```bash
python synergy_analyzer.py
```

**Research Basis:**
- Expert strategy patterns from high-Ascension play
- Documented synergies from Slay the Spire Wiki and community resources
- Card interaction analysis from game mechanics

### 2. Path Optimizer (`path_optimizer.py`)

Recommends optimal paths through the procedural map using entropy-based heuristics derived from AI/ML research.

**Features:**
- Evaluates path quality using entropy metrics
- Estimates HP costs and expected value
- Balances risk vs. reward based on game state
- Provides research-backed recommendations

**Usage:**
```python
from path_optimizer import PathOptimizer, GameState, NodeType

optimizer = PathOptimizer()
optimizer.risk_tolerance = 0.7  # Moderately aggressive

# Define game state
state = GameState(
    current_hp=65,
    max_hp=80,
    gold=120,
    current_act=1,
    floor=3,
    deck_power=4.0,
    potion_count=2,
    has_key_relics=False
)

# Get recommendation
available = [NodeType.MONSTER, NodeType.ELITE, NodeType.SHOP]
recommended, analysis = optimizer.recommend_next_node(available, state)
```

**Run Example:**
```bash
python path_optimizer.py
```

**Research Basis:**
- "Analysis of Uncertainty in Procedural Maps in Slay the Spire" (arXiv 2025)
- "Using machine learning to help find paths through the map" (Malmö University 2021)
- Key findings: Higher-entropy paths correlate with winning; elite fights critical despite risk

## Integration with Main Repository

These tools complement the existing simulation framework:

- **Synergy Analyzer** can inform card selection in `card_loader.py`
- **Path Optimizer** can guide node selection in procedural generation
- Both tools can be integrated into `orchestrator_unified.py` for automated decision-making

## Future Enhancements

### Planned Features

1. **Quantum-Inspired Optimization**
   - Apply quantum probability models to decision-making
   - Model superposition of strategies
   - Use interference effects for synergy detection

2. **Machine Learning Integration**
   - Train neural networks on expert gameplay
   - Reinforcement learning for combat decisions
   - Transfer learning across characters

3. **Real-Time Integration**
   - Game state extraction via ModTheSpire API
   - Live recommendations during gameplay
   - Adaptive learning from player decisions

4. **Advanced Analytics**
   - Win rate prediction based on deck state
   - Counterfactual analysis ("what if" scenarios)
   - Meta-strategy identification

## Quantum Decision Theory Applications

Based on research in Quantizing Economics, potential applications include:

### 1. Superposition of Strategies
Model player's deck-building intention as quantum superposition:
- Multiple potential archetypes exist simultaneously
- Key card/relic acquisition "collapses" to one strategy
- Interference effects explain anti-synergies

### 2. Entanglement Modeling
Capture deep interdependencies:
- Card value depends on other cards (non-local effects)
- Relic acquisition affects entire deck retroactively
- System-level properties emerge from interactions

### 3. Measurement Effects
Recognize that decisions change game state:
- Choosing a card reveals information, affecting future offerings
- Path selection influences event outcomes
- Strategic observation itself alters probabilities

## Research References

### Slay the Spire AI/ML
- [Using machine learning to help find paths through the map in Slay the Spire](https://www.diva-portal.org/smash/get/diva2:1565751/FULLTEXT02.pdf)
- [Analysis of Uncertainty in Procedural Maps in Slay the Spire (arXiv)](https://arxiv.org/html/2504.03918v1)
- [Are You Lucky or Skilled? (IEEE)](https://aeau.github.io/assets/papers/2023/andersson2023-cog03.pdf)

### Quantum Economics
- [Quantum Economics by David Orrell](https://books.google.com/books/about/Quantum_Economics.html?id=9YlZDwAAQBAJ)
- [Quantum propensity in economics (arXiv)](https://arxiv.org/pdf/2103.10938)
- [A systematic literature review on quantum economics](https://armgpublishing.com/wp-content/uploads/2024/04/SEC_1_2024_5.pdf)

### Game Design
- [Slay the Spire: Metrics Driven Design and Balance (GDC Vault)](https://www.gdcvault.com/play/1025731/-Slay-the-Spire-Metrics)

## Contributing

To add new tools or enhance existing ones:

1. Follow existing code structure and documentation style
2. Include research references for algorithmic decisions
3. Provide example usage and test cases
4. Update this README with new features

## License

These tools are part of the STS-HELP repository. See main LICENSE file for details.

---

**Last Updated:** February 2026  
**Status:** Prototype tools for research and development  
**Maintainers:** STS-HELP Development Team
