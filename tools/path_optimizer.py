#!/usr/bin/env python3
"""
Path Optimizer for Slay the Spire

This tool recommends optimal paths through the procedural map using entropy-based
heuristics derived from AI/ML research. Based on findings from academic papers
showing that higher-entropy (riskier) paths correlate with winning.

Research basis:
- "Analysis of Uncertainty in Procedural Maps in Slay the Spire" (arXiv)
- "Using machine learning to help find paths through the map" (Malmö University)
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
    """Types of nodes in the Slay the Spire map."""
    MONSTER = 'M'
    ELITE = 'E'
    REST = 'R'
    SHOP = '$'
    EVENT = '?'
    TREASURE = 'T'
    BOSS = 'B'


@dataclass
class GameState:
    """Represents current game state for path planning."""
    current_hp: int
    max_hp: int
    gold: int
    current_act: int
    floor: int
    deck_power: float  # Subjective rating 0-10
    potion_count: int
    has_key_relics: bool  # Whether deck has build-defining relics
    

@dataclass
class PathSegment:
    """Represents a potential path through the map."""
    nodes: List[NodeType]
    expected_value: float
    risk_score: float
    entropy: float
    reasons: List[str]


class PathOptimizer:
    """Optimizes path selection through Slay the Spire maps."""
    
    # Node values based on research (relative importance)
    NODE_VALUES = {
        NodeType.ELITE: 10.0,      # High value (relics) but risky
        NodeType.REST: 7.0,         # Critical for HP/upgrades
        NodeType.SHOP: 6.0,         # Gold-dependent value
        NodeType.TREASURE: 8.0,     # Free relic (Act 1 only)
        NodeType.EVENT: 5.0,        # High variance
        NodeType.MONSTER: 3.0,      # Basic rewards
        NodeType.BOSS: 15.0,        # Required, high value
    }
    
    # HP cost estimates (in % of max HP)
    HP_COSTS = {
        NodeType.ELITE: 0.25,       # ~25% HP loss
        NodeType.MONSTER: 0.10,     # ~10% HP loss
        NodeType.EVENT: 0.05,       # Variable, but some risk
        NodeType.REST: -0.30,       # Heals 30%
        NodeType.SHOP: 0.0,
        NodeType.TREASURE: 0.0,
        NodeType.BOSS: 0.35,        # ~35% HP loss
    }
    
    def __init__(self):
        """Initialize the path optimizer."""
        self.risk_tolerance = 0.7  # Default: moderately aggressive
    
    def calculate_entropy(self, nodes: List[NodeType]) -> float:
        """Calculate Shannon entropy of a path.
        
        Higher entropy = more diverse/unpredictable path.
        Research shows winning players take higher-entropy paths.
        
        Args:
            nodes: List of node types in path
            
        Returns:
            Entropy value (higher = more diverse)
        """
        if not nodes:
            return 0.0
        
        # Count occurrences of each node type
        counts = {}
        for node in nodes:
            counts[node] = counts.get(node, 0) + 1
        
        # Calculate Shannon entropy
        total = len(nodes)
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy
    
    def estimate_hp_change(self, nodes: List[NodeType], 
                          state: GameState) -> Tuple[int, int]:
        """Estimate HP change along a path.
        
        Args:
            nodes: Path nodes
            state: Current game state
            
        Returns:
            Tuple of (expected_hp_change, worst_case_hp_change)
        """
        expected_change = 0.0
        worst_case = 0.0
        
        for node in nodes:
            base_cost = self.HP_COSTS.get(node, 0.0)
            hp_change = base_cost * state.max_hp
            
            # Adjust for deck power
            if node in [NodeType.ELITE, NodeType.MONSTER, NodeType.BOSS]:
                # Stronger deck takes less damage
                power_modifier = 1.0 - (state.deck_power / 20.0)
                hp_change *= power_modifier
            
            expected_change += hp_change
            
            # Worst case: 1.5x expected damage
            if hp_change < 0:  # Negative = HP loss
                worst_case += hp_change * 1.5
            else:
                worst_case += hp_change
        
        return (int(expected_change), int(worst_case))
    
    def evaluate_path(self, nodes: List[NodeType], 
                     state: GameState) -> PathSegment:
        """Evaluate a potential path through the map.
        
        Args:
            nodes: List of nodes in the path
            state: Current game state
            
        Returns:
            PathSegment with evaluation results
        """
        # Calculate base value
        base_value = sum(self.NODE_VALUES.get(n, 0) for n in nodes)
        
        # Calculate entropy
        entropy = self.calculate_entropy(nodes)
        
        # Estimate HP costs
        expected_hp, worst_hp = self.estimate_hp_change(nodes, state)
        
        # Calculate risk score (0-1, higher = riskier)
        hp_after = state.current_hp + expected_hp
        hp_ratio = hp_after / state.max_hp if state.max_hp > 0 else 0
        
        # Risk factors
        risk_score = 0.0
        reasons = []
        
        # Elite count risk
        elite_count = sum(1 for n in nodes if n == NodeType.ELITE)
        if elite_count > 0:
            risk_score += elite_count * 0.2
            reasons.append(f"{elite_count} elite(s) - high reward but risky")
        
        # Event variance risk
        event_count = sum(1 for n in nodes if n == NodeType.EVENT)
        if event_count > 2:
            risk_score += 0.15
            reasons.append(f"{event_count} events - high variance")
        
        # HP danger zone
        if hp_ratio < 0.3:
            risk_score += 0.3
            reasons.append("Low HP after path - dangerous")
        elif hp_ratio < 0.5:
            risk_score += 0.15
            reasons.append("Moderate HP after path")
        
        # Adjust value based on game state
        adjusted_value = base_value
        
        # Early game: prioritize elites for relics
        if state.floor < 10 and not state.has_key_relics:
            elite_bonus = elite_count * 3.0
            adjusted_value += elite_bonus
            if elite_count > 0:
                reasons.append("Early elites recommended for key relics")
        
        # Low HP: value rest sites more
        if state.current_hp < state.max_hp * 0.4:
            rest_count = sum(1 for n in nodes if n == NodeType.REST)
            rest_bonus = rest_count * 5.0
            adjusted_value += rest_bonus
            if rest_count > 0:
                reasons.append("Rest sites critical for HP recovery")
        
        # Gold availability for shops
        shop_count = sum(1 for n in nodes if n == NodeType.SHOP)
        if shop_count > 0:
            if state.gold < 100:
                adjusted_value -= 2.0 * shop_count
                reasons.append("Limited gold reduces shop value")
            elif state.gold > 300:
                adjusted_value += 2.0 * shop_count
                reasons.append("High gold makes shops valuable")
        
        # Research-based entropy bonus
        # Higher entropy correlates with winning (within reason)
        entropy_bonus = entropy * 2.0
        adjusted_value += entropy_bonus
        
        # Calculate final expected value
        # Balance value against risk based on tolerance
        expected_value = adjusted_value - (risk_score * (1 - self.risk_tolerance) * 5)
        
        return PathSegment(
            nodes=nodes,
            expected_value=expected_value,
            risk_score=risk_score,
            entropy=entropy,
            reasons=reasons
        )
    
    def recommend_next_node(self, available_nodes: List[NodeType],
                           state: GameState, 
                           look_ahead: int = 1) -> Tuple[NodeType, PathSegment]:
        """Recommend the best next node to visit.
        
        Args:
            available_nodes: List of nodes currently available
            state: Current game state
            look_ahead: How many nodes ahead to consider (1-3)
            
        Returns:
            Tuple of (recommended_node, path_analysis)
        """
        if not available_nodes:
            raise ValueError("No available nodes to choose from")
        
        # Evaluate each immediate option
        best_node = None
        best_evaluation = None
        best_score = float('-inf')
        
        for node in available_nodes:
            # Simple evaluation: just this node
            if look_ahead <= 1:
                path = [node]
                evaluation = self.evaluate_path(path, state)
                score = evaluation.expected_value
            else:
                # More complex: consider potential follow-ups
                # For simplicity, use a heuristic based on node type patterns
                path = self._generate_likely_continuation([node], look_ahead)
                evaluation = self.evaluate_path(path, state)
                score = evaluation.expected_value
            
            if score > best_score:
                best_score = score
                best_node = node
                best_evaluation = evaluation
        
        return (best_node, best_evaluation)
    
    def _generate_likely_continuation(self, initial_path: List[NodeType],
                                      total_length: int) -> List[NodeType]:
        """Generate a likely continuation of a path for lookahead.
        
        Args:
            initial_path: Starting path segment
            total_length: Desired total path length
            
        Returns:
            Extended path
        """
        path = initial_path.copy()
        
        # Simple heuristic: alternate between combat and utility
        last_combat = path[-1] in [NodeType.ELITE, NodeType.MONSTER]
        
        while len(path) < total_length:
            if last_combat:
                # After combat, prefer rest/shop
                path.append(NodeType.REST if len(path) % 3 == 0 else NodeType.SHOP)
                last_combat = False
            else:
                # After utility, prefer combat (monster or elite)
                path.append(NodeType.ELITE if len(path) % 4 == 0 else NodeType.MONSTER)
                last_combat = True
        
        return path
    
    def analyze_full_act_path(self, path: List[NodeType],
                              state: GameState) -> Dict:
        """Analyze a complete path through an act.
        
        Args:
            path: Full path from start to boss
            state: Starting game state
            
        Returns:
            Comprehensive analysis dictionary
        """
        evaluation = self.evaluate_path(path, state)
        expected_hp, worst_hp = self.estimate_hp_change(path, state)
        
        # Count node types
        node_counts = {}
        for node in path:
            node_counts[node] = node_counts.get(node, 0) + 1
        
        # Generate strategic assessment
        assessment = []
        
        # Elite count
        elites = node_counts.get(NodeType.ELITE, 0)
        if elites >= 3:
            assessment.append("Aggressive elite hunting - high relic count expected")
        elif elites == 2:
            assessment.append("Standard elite count - balanced approach")
        else:
            assessment.append("Conservative elite count - safer but fewer relics")
        
        # Rest vs. Upgrade balance
        rests = node_counts.get(NodeType.REST, 0)
        if rests >= 3:
            assessment.append("Multiple rest opportunities - HP recovery assured")
        elif rests == 2:
            assessment.append("Standard rest count - plan upgrades carefully")
        else:
            assessment.append("Few rest sites - HP management critical")
        
        # Entropy assessment
        if evaluation.entropy > 2.0:
            assessment.append("High path entropy - diverse and adaptive strategy")
        elif evaluation.entropy > 1.5:
            assessment.append("Moderate entropy - balanced path")
        else:
            assessment.append("Low entropy - predictable, possibly too safe")
        
        return {
            'evaluation': evaluation,
            'node_counts': node_counts,
            'expected_hp_change': expected_hp,
            'worst_case_hp': worst_hp,
            'final_hp_estimate': state.current_hp + expected_hp,
            'assessment': assessment,
            'research_notes': [
                "Research shows winning players take higher-entropy paths",
                f"Elite count of {elites} is {'optimal' if elites >= 2 else 'suboptimal'} for scaling",
                f"Path entropy of {evaluation.entropy:.2f} {'correlates with' if evaluation.entropy > 1.8 else 'may not align with'} winning patterns"
            ]
        }


def main():
    """Example usage of the Path Optimizer."""
    print("=== Slay the Spire Path Optimizer ===\n")
    print("Based on AI/ML research showing that higher-entropy paths correlate with winning.\n")
    
    # Initialize optimizer
    optimizer = PathOptimizer()
    optimizer.risk_tolerance = 0.7  # Moderately aggressive
    
    # Example game state (early Act 1)
    state = GameState(
        current_hp=65,
        max_hp=80,
        gold=120,
        current_act=1,
        floor=3,
        deck_power=4.0,  # Still building
        potion_count=2,
        has_key_relics=False
    )
    
    print("Current State:")
    print(f"  HP: {state.current_hp}/{state.max_hp}")
    print(f"  Gold: {state.gold}")
    print(f"  Floor: {state.floor} (Act {state.current_act})")
    print(f"  Deck Power: {state.deck_power}/10\n")
    
    # Example: Choose next node
    available = [NodeType.MONSTER, NodeType.ELITE, NodeType.SHOP]
    
    print("Available nodes:", [n.value for n in available])
    
    recommended, analysis = optimizer.recommend_next_node(available, state, look_ahead=2)
    
    print(f"\nRecommended: {recommended.value} ({recommended.name})")
    print(f"Expected Value: {analysis.expected_value:.1f}")
    print(f"Risk Score: {analysis.risk_score:.2f}")
    print(f"Path Entropy: {analysis.entropy:.2f}")
    
    if analysis.reasons:
        print("\nReasons:")
        for reason in analysis.reasons:
            print(f"  • {reason}")
    
    # Example: Analyze a full Act 1 path
    print("\n" + "="*50)
    print("Full Act 1 Path Analysis\n")
    
    example_path = [
        NodeType.MONSTER, NodeType.MONSTER, NodeType.ELITE,
        NodeType.REST, NodeType.MONSTER, NodeType.SHOP,
        NodeType.ELITE, NodeType.REST, NodeType.MONSTER,
        NodeType.ELITE, NodeType.MONSTER, NodeType.REST,
        NodeType.SHOP, NodeType.MONSTER, NodeType.BOSS
    ]
    
    print("Path:", " → ".join([n.value for n in example_path]))
    
    full_analysis = optimizer.analyze_full_act_path(example_path, state)
    
    print(f"\nNode Breakdown:")
    for node_type, count in full_analysis['node_counts'].items():
        print(f"  {node_type.name}: {count}")
    
    print(f"\nHP Projection:")
    print(f"  Expected change: {full_analysis['expected_hp_change']:+d}")
    print(f"  Final HP estimate: {full_analysis['final_hp_estimate']}/{state.max_hp}")
    print(f"  Worst case: {full_analysis['worst_case_hp']:+d}")
    
    print(f"\nPath Entropy: {full_analysis['evaluation'].entropy:.2f}")
    print(f"Overall Value: {full_analysis['evaluation'].expected_value:.1f}")
    print(f"Risk Score: {full_analysis['evaluation'].risk_score:.2f}")
    
    print("\nStrategic Assessment:")
    for note in full_analysis['assessment']:
        print(f"  • {note}")
    
    print("\nResearch-Based Insights:")
    for note in full_analysis['research_notes']:
        print(f"  • {note}")


if __name__ == '__main__':
    main()
