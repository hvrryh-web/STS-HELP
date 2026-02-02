"""
Enhanced AI with lookahead evaluation for Slay the Spire simulation.

Implements multi-turn planning and improved heuristics for card selection.
Resolution for E1: Greedy card selection AI.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
import numpy as np

from engine_common import (
    Card, CardType, PlayerState, EnemyState, DeckState,
    apply_damage_to_enemy, apply_damage_to_player, get_playable_cards
)


class PlayStyle(Enum):
    """AI play style enumeration."""
    GREEDY = "greedy"           # Maximize immediate damage
    DEFENSIVE = "defensive"     # Prioritize blocking
    BALANCED = "balanced"       # Balance damage and defense
    SCALING = "scaling"         # Prioritize long-term scaling


@dataclass
class TurnSimulationResult:
    """Result of simulating a single turn."""
    player_hp: int
    enemy_hp: int
    player_block: int
    enemy_block: int
    cards_played: List[str]
    damage_dealt: int
    damage_taken: int
    buffs_applied: Dict[str, int]


@dataclass
class LookaheadResult:
    """Result of multi-turn lookahead evaluation."""
    expected_win_rate: float
    expected_hp_remaining: float
    expected_turns: float
    best_card: Optional[Card]
    card_values: Dict[str, float]
    reasoning: str


class LookaheadAI:
    """
    AI with multi-turn lookahead evaluation.
    
    Features:
    - 2-turn lookahead with Monte Carlo sampling
    - Improved heuristics for scaling cards (powers, strength-building)
    - Risk-adjusted card selection based on enemy intent
    - Synergy-aware evaluation
    """
    
    def __init__(
        self,
        depth: int = 2,
        samples: int = 10,
        play_style: PlayStyle = PlayStyle.BALANCED
    ):
        """
        Initialize lookahead AI.
        
        Args:
            depth: Number of turns to look ahead.
            samples: Monte Carlo samples per evaluation.
            play_style: AI play style preference.
        """
        self.depth = depth
        self.samples = samples
        self.play_style = play_style
        
        # Style-based weights
        self.style_weights = {
            PlayStyle.GREEDY: {'damage': 1.5, 'block': 0.8, 'scaling': 0.5},
            PlayStyle.DEFENSIVE: {'damage': 0.8, 'block': 1.5, 'scaling': 0.7},
            PlayStyle.BALANCED: {'damage': 1.0, 'block': 1.0, 'scaling': 1.0},
            PlayStyle.SCALING: {'damage': 0.7, 'block': 0.9, 'scaling': 1.8},
        }
    
    def evaluate_card(
        self,
        card: Card,
        player: PlayerState,
        enemy: EnemyState,
        deck_state: DeckState,
        turn: int = 1
    ) -> float:
        """
        Evaluate a card with improved heuristics.
        
        Args:
            card: Card to evaluate.
            player: Player state.
            enemy: Enemy state.
            deck_state: Deck state.
            turn: Current turn number.
        
        Returns:
            Estimated value of playing the card.
        """
        value = 0.0
        effects = card.effects
        weights = self.style_weights[self.play_style]
        
        # === IMMEDIATE DAMAGE VALUE ===
        if 'damage' in effects:
            base_damage = effects['damage']
            
            # Apply strength scaling correctly
            if 'strength_multiplier' in effects:
                # Heavy Blade: Strength affects this card 3x (or 5x upgraded)
                multiplier = effects['strength_multiplier']
                total_damage = base_damage + (player.strength * multiplier)
            else:
                total_damage = base_damage + player.strength
            
            # Multi-hit cards
            if 'hits' in effects:
                hits = effects['hits']
                # Each hit gets strength bonus
                total_damage = (base_damage + player.strength) * hits
            
            # Apply vulnerability (50% more damage)
            if enemy.vulnerable > 0:
                total_damage = int(total_damage * 1.5)
            
            # Damage value relative to enemy HP (killing blow is highly valuable)
            if total_damage >= enemy.hp:
                # Killing blow - maximum value
                value += enemy.hp * 2.0 * weights['damage']
            else:
                # Proportional value
                value += total_damage * weights['damage']
        
        # === BLOCK VALUE ===
        if 'block' in effects:
            base_block = effects['block']
            # Apply dexterity bonus
            block_amount = base_block + player.dexterity
            # Apply frail penalty if player is frailed (25% less block)
            if hasattr(player, 'frail') and player.frail > 0:
                block_amount = int(block_amount * 0.75)
            
            # Value block based on enemy intent
            if enemy.intent.value == 'attack':
                incoming = enemy.intent_value + enemy.strength
                if enemy.weak > 0:
                    incoming = int(incoming * 0.75)
                
                # Check for multi-hit attacks (intent_hits attribute or pattern)
                hits = getattr(enemy, 'intent_hits', 1)
                total_incoming = incoming * hits
                
                # Block is valuable up to the amount of incoming damage
                effective_block = min(block_amount, max(0, total_incoming - player.block))
                value += effective_block * 1.5 * weights['block']
                
                # Extra block has value for future turns or multi-hit remaining
                excess_block = block_amount - effective_block
                # Higher value if combat will be long (enemy has high HP)
                turns_remaining = max(1, enemy.hp // 15)
                excess_multiplier = 0.3 + min(0.3, turns_remaining * 0.05)
                value += excess_block * excess_multiplier * weights['block']
            else:
                # No attack incoming - block has reduced but non-zero value
                # Proactive blocking for future turns
                turns_remaining = max(1, enemy.hp // 15)
                value += block_amount * (0.4 + min(0.2, turns_remaining * 0.03)) * weights['block']
        
        # === SCALING VALUE (LONG-TERM) ===
        
        # Strength gain
        if 'strength' in effects:
            strength_gain = effects['strength']
            # Estimate remaining damage cards in deck
            remaining_attacks = sum(
                1 for c in deck_state.draw_pile + deck_state.hand + deck_state.discard_pile
                if c.card_type == CardType.ATTACK
            )
            # Estimate remaining turns
            estimated_turns = max(3, enemy.hp // 15)
            
            # Strength value scales with attacks remaining and turns
            strength_value = strength_gain * remaining_attacks * 0.8 * estimated_turns / 5
            value += strength_value * weights['scaling']
        
        # Strength per turn (Demon Form)
        if 'strength_per_turn' in effects:
            strength_per_turn = effects['strength_per_turn']
            estimated_turns = max(3, enemy.hp // 15)
            
            # Very high value for scaling - compounds over time
            # Turns 2+3+4+... = roughly turns^2 / 2 total strength gained
            total_estimated_strength = strength_per_turn * estimated_turns * (estimated_turns + 1) / 2
            remaining_attacks = sum(
                1 for c in deck_state.draw_pile + deck_state.hand + deck_state.discard_pile
                if c.card_type == CardType.ATTACK
            )
            value += total_estimated_strength * remaining_attacks * 0.3 * weights['scaling']
        
        # Double strength (Limit Break)
        if effects.get('double_strength'):
            # Value is proportional to current strength
            if player.strength > 0:
                value += player.strength * 8 * weights['scaling']
            else:
                value += 0.5  # Minimal value if no strength
        
        # === DEBUFF VALUE ===
        
        # Vulnerable application
        if 'vulnerable' in effects:
            vuln_stacks = effects['vulnerable']
            # Estimate future damage output
            remaining_attacks = sum(
                1 for c in deck_state.draw_pile + deck_state.hand
                if c.card_type == CardType.ATTACK and c != card
            )
            avg_damage_per_attack = 8 + player.strength  # rough estimate
            
            # Each vuln stack = 50% more damage for one turn
            vuln_value = vuln_stacks * remaining_attacks * avg_damage_per_attack * 0.5 * 0.5
            value += vuln_value
        
        # Weak application (reduces incoming damage)
        if 'weak' in effects:
            weak_stacks = effects['weak']
            # Estimate incoming damage
            avg_enemy_damage = enemy.intent_value if enemy.intent.value == 'attack' else 10
            weak_value = weak_stacks * avg_enemy_damage * 0.25
            value += weak_value * weights['block']
        
        # Poison application
        if 'poison' in effects:
            poison_amount = effects['poison']
            # When applying new poison, total damage over the fight is:
            # (current_poison + new_poison) * (current_poison + new_poison + 1) / 2
            # But we only credit the incremental damage from NEW poison
            current_poison = enemy.poison
            new_total = current_poison + poison_amount
            # Triangular number: sum from 1 to n = n*(n+1)/2
            damage_with_new = new_total * (new_total + 1) / 2
            damage_without_new = current_poison * (current_poison + 1) / 2
            incremental_damage = damage_with_new - damage_without_new
            # Cap at enemy remaining HP
            incremental_damage = min(incremental_damage, enemy.hp)
            value += incremental_damage * 0.9
        
        # Double/Triple poison (Catalyst)
        if effects.get('double_poison') or effects.get('triple_poison'):
            if enemy.poison > 0:
                current_poison = enemy.poison
                # Catalyst doubles (or triples if upgraded) current poison
                multiplier = 3 if effects.get('triple_poison') else 2
                new_poison = current_poison * multiplier
                # Calculate incremental damage from the multiplication
                damage_with_new = new_poison * (new_poison + 1) / 2
                damage_without_mult = current_poison * (current_poison + 1) / 2
                incremental = min(damage_with_new - damage_without_mult, enemy.hp)
                value += incremental * 0.9
        
        # === CARD DRAW VALUE ===
        if 'draw' in effects:
            draw_count = effects['draw']
            # Draw is valuable, especially early in combat
            draw_value = draw_count * (5 if turn <= 2 else 3)
            value += draw_value
        
        # === ENERGY VALUE ===
        if 'energy' in effects:
            energy_gain = effects['energy']
            # Each energy is worth roughly one card play
            value += energy_gain * 6
        
        # === HP LOSS COST ===
        if 'hp_loss' in effects:
            hp_cost = effects['hp_loss']
            # HP is precious, especially at low HP
            hp_ratio = player.hp / player.max_hp
            if hp_ratio < 0.3:
                value -= hp_cost * 4  # High penalty at low HP
            elif hp_ratio < 0.5:
                value -= hp_cost * 2
            else:
                value -= hp_cost * 1
        
        # === EXHAUST CONSIDERATION ===
        if card.exhaust:
            # Exhaust reduces value somewhat (card is gone)
            # But exhaust synergies can offset this
            value -= 1.0
        
        # === ENERGY EFFICIENCY ===
        if card.cost > 0:
            value = value / card.cost
        elif card.cost == 0:
            value *= 1.2  # Zero-cost cards are efficient
        
        return value
    
    def select_card_to_play(
        self,
        deck_state: DeckState,
        player: PlayerState,
        enemy: EnemyState,
        turn: int = 1,
        rng: Optional[np.random.Generator] = None
    ) -> Tuple[Optional[Card], float]:
        """
        Select the best card to play from hand.
        
        Args:
            deck_state: Current deck state.
            player: Player state.
            enemy: Enemy state.
            turn: Current turn number.
            rng: Random number generator for lookahead.
        
        Returns:
            Tuple of (best card, value) or (None, 0) if no card should be played.
        """
        playable = get_playable_cards(deck_state, player)
        
        if not playable:
            return None, 0.0
        
        best_card = None
        best_value = -float('inf')
        
        for card in playable:
            if self.depth > 0 and rng is not None:
                # Use lookahead evaluation
                value = self._evaluate_with_lookahead(
                    card, player, enemy, deck_state, turn, rng
                )
            else:
                # Use immediate evaluation
                value = self.evaluate_card(card, player, enemy, deck_state, turn)
            
            if value > best_value:
                best_value = value
                best_card = card
        
        # Check if ending turn is better (block is sufficient, save cards)
        if best_value < 1.0 and player.block >= enemy.intent_value + enemy.strength:
            # Already have enough block, maybe save cards
            return None, 0.0
        
        return best_card if best_value > 0 else None, best_value
    
    def _evaluate_with_lookahead(
        self,
        card: Card,
        player: PlayerState,
        enemy: EnemyState,
        deck_state: DeckState,
        turn: int,
        rng: np.random.Generator
    ) -> float:
        """
        Evaluate a card using Monte Carlo lookahead.
        
        Args:
            card: Card to evaluate.
            player: Player state.
            enemy: Enemy state.
            deck_state: Deck state.
            turn: Current turn.
            rng: Random number generator.
        
        Returns:
            Expected value of playing the card.
        """
        total_value = 0.0
        
        for _ in range(self.samples):
            # Clone states
            sim_player = self._clone_player(player)
            sim_enemy = self._clone_enemy(enemy)
            sim_deck = self._clone_deck(deck_state)
            sim_rng = np.random.default_rng(rng.integers(2**31))
            
            # Play the card being evaluated
            immediate_value = self.evaluate_card(card, sim_player, sim_enemy, sim_deck, turn)
            self._simulate_card_play(card, sim_player, sim_enemy, sim_deck, sim_rng)
            
            # Simulate remaining turn
            turn_value = self._simulate_rest_of_turn(sim_player, sim_enemy, sim_deck, turn, sim_rng)
            
            # Simulate future turns (simplified)
            future_value = 0.0
            for future_turn in range(1, self.depth):
                discount = 0.9 ** future_turn
                self._simulate_enemy_turn(sim_player, sim_enemy, sim_rng)
                
                if sim_player.hp <= 0:
                    future_value -= 100 * discount  # Death is very bad
                    break
                if sim_enemy.hp <= 0:
                    future_value += 50 * discount  # Win is good
                    break
                
                sim_player.block = 0
                sim_player.energy = sim_player.max_energy
                sim_deck.draw_cards(5, sim_rng)
                
                turn_val = self._simulate_full_turn(sim_player, sim_enemy, sim_deck, turn + future_turn, sim_rng)
                future_value += turn_val * discount
            
            total_value += immediate_value + turn_value + future_value
        
        return total_value / self.samples
    
    def _simulate_card_play(
        self,
        card: Card,
        player: PlayerState,
        enemy: EnemyState,
        deck_state: DeckState,
        rng: np.random.Generator
    ) -> None:
        """Simulate playing a card (simplified)."""
        player.energy -= card.cost
        effects = card.effects
        
        # Damage
        if 'damage' in effects:
            base = effects['damage']
            if 'strength_multiplier' in effects:
                total = base + player.strength * effects['strength_multiplier']
            else:
                total = base + player.strength
            
            if 'hits' in effects:
                total = (base + player.strength) * effects['hits']
            
            if enemy.vulnerable > 0:
                total = int(total * 1.5)
            
            enemy.hp -= max(0, total - enemy.block)
            enemy.block = max(0, enemy.block - total)
        
        # Block
        if 'block' in effects:
            player.block += effects['block'] + player.dexterity
        
        # Strength
        if 'strength' in effects:
            player.strength += effects['strength']
        if effects.get('double_strength'):
            player.strength *= 2
        
        # Handle card destination
        if card.exhaust:
            deck_state.exhaust_card(card)
        else:
            deck_state.discard_card(card)
    
    def _simulate_rest_of_turn(
        self,
        player: PlayerState,
        enemy: EnemyState,
        deck_state: DeckState,
        turn: int,
        rng: np.random.Generator
    ) -> float:
        """Simulate rest of the turn with heuristic play."""
        value = 0.0
        
        while player.energy > 0 and enemy.hp > 0:
            playable = get_playable_cards(deck_state, player)
            if not playable:
                break
            
            # Quick heuristic selection
            best_card = None
            best_val = -float('inf')
            for c in playable:
                val = self.evaluate_card(c, player, enemy, deck_state, turn)
                if val > best_val:
                    best_val = val
                    best_card = c
            
            if best_card is None or best_val <= 0:
                break
            
            self._simulate_card_play(best_card, player, enemy, deck_state, rng)
            value += best_val * 0.5  # Discounted for being future cards
        
        return value
    
    def _simulate_full_turn(
        self,
        player: PlayerState,
        enemy: EnemyState,
        deck_state: DeckState,
        turn: int,
        rng: np.random.Generator
    ) -> float:
        """Simulate a full turn."""
        return self._simulate_rest_of_turn(player, enemy, deck_state, turn, rng)
    
    def _simulate_enemy_turn(
        self,
        player: PlayerState,
        enemy: EnemyState,
        rng: np.random.Generator
    ) -> None:
        """Simulate enemy turn (simplified)."""
        # Simplified enemy action - attack
        damage = enemy.intent_value + enemy.strength
        if enemy.weak > 0:
            damage = int(damage * 0.75)
            enemy.weak -= 1
        
        if player.block >= damage:
            player.block -= damage
        else:
            player.hp -= (damage - player.block)
            player.block = 0
        
        # Decrement debuffs
        if enemy.vulnerable > 0:
            enemy.vulnerable -= 1
    
    def _clone_player(self, player: PlayerState) -> PlayerState:
        """Create a shallow copy of player state."""
        return PlayerState(
            hp=player.hp,
            max_hp=player.max_hp,
            block=player.block,
            energy=player.energy,
            max_energy=player.max_energy,
            strength=player.strength,
            dexterity=player.dexterity,
            artifact=player.artifact,
            poison=player.poison,
            orbs=list(player.orbs),
            orb_slots=player.orb_slots,
            stance=player.stance,
            relics=list(player.relics)
        )
    
    def _clone_enemy(self, enemy: EnemyState) -> EnemyState:
        """Create a shallow copy of enemy state."""
        return EnemyState(
            name=enemy.name,
            hp=enemy.hp,
            max_hp=enemy.max_hp,
            block=enemy.block,
            strength=enemy.strength,
            poison=enemy.poison,
            vulnerable=enemy.vulnerable,
            weak=enemy.weak,
            artifact=enemy.artifact,
            intent=enemy.intent,
            intent_value=enemy.intent_value
        )
    
    def _clone_deck(self, deck_state: DeckState) -> DeckState:
        """Create a shallow copy of deck state."""
        return DeckState(
            draw_pile=[c.copy() for c in deck_state.draw_pile],
            hand=[c.copy() for c in deck_state.hand],
            discard_pile=[c.copy() for c in deck_state.discard_pile],
            exhaust_pile=[c.copy() for c in deck_state.exhaust_pile],
            hand_limit=deck_state.hand_limit
        )


def evaluate_card_reward(
    candidates: List[Card],
    current_deck: List[Card],
    upcoming_enemy: EnemyState,
    player: PlayerState,
    rng: np.random.Generator,
    simulations: int = 100
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate card reward options by simulating combats.
    
    Args:
        candidates: List of candidate cards (including "Skip" as None).
        current_deck: Current deck.
        upcoming_enemy: Next enemy to fight.
        player: Player state.
        rng: Random number generator.
        simulations: Number of simulations per card.
    
    Returns:
        Dictionary mapping card name to evaluation results.
    """
    # Local import to avoid circular dependency - ironclad_engine imports from engine_common
    # which is also used by this module. This function is optional and only called when
    # actually evaluating card rewards with the Ironclad engine.
    from ironclad_engine import simulate_combat
    
    results = {}
    ai = LookaheadAI(depth=1, samples=5)
    
    # Baseline: current deck (Skip option)
    baseline_wins = 0
    baseline_hp = []
    baseline_turns = []
    
    for _ in range(simulations):
        sim_rng = np.random.default_rng(rng.integers(2**31))
        sim_player = PlayerState(hp=player.hp, max_hp=player.max_hp)
        sim_enemy = EnemyState(hp=upcoming_enemy.hp, max_hp=upcoming_enemy.max_hp)
        
        result = simulate_combat(sim_player, sim_enemy, current_deck, sim_rng)
        
        if result.win:
            baseline_wins += 1
        baseline_hp.append(result.final_hp)
        baseline_turns.append(result.turns)
    
    baseline_win_rate = baseline_wins / simulations
    baseline_avg_hp = np.mean(baseline_hp)
    
    results["Skip"] = {
        "win_rate": baseline_win_rate,
        "avg_hp_remaining": baseline_avg_hp,
        "avg_turns": np.mean(baseline_turns),
        "delta_win_rate": 0.0,
        "delta_hp": 0.0,
        "recommendation": "Skip",
        "reasoning": "Keep deck lean and consistent"
    }
    
    # Evaluate each candidate card
    for card in candidates:
        if card is None:
            continue
        
        deck_with_card = current_deck + [card]
        card_wins = 0
        card_hp = []
        card_turns = []
        
        for _ in range(simulations):
            sim_rng = np.random.default_rng(rng.integers(2**31))
            sim_player = PlayerState(hp=player.hp, max_hp=player.max_hp)
            sim_enemy = EnemyState(hp=upcoming_enemy.hp, max_hp=upcoming_enemy.max_hp)
            
            result = simulate_combat(sim_player, sim_enemy, deck_with_card, sim_rng)
            
            if result.win:
                card_wins += 1
            card_hp.append(result.final_hp)
            card_turns.append(result.turns)
        
        win_rate = card_wins / simulations
        avg_hp = np.mean(card_hp)
        delta_win = win_rate - baseline_win_rate
        delta_hp = avg_hp - baseline_avg_hp
        
        # Generate reasoning
        if delta_win > 0.05:
            reasoning = f"Significant win rate improvement (+{delta_win:.1%})"
        elif delta_win > 0.01:
            reasoning = f"Modest improvement (+{delta_win:.1%})"
        elif delta_win < -0.01:
            reasoning = f"May dilute deck (win rate -{abs(delta_win):.1%})"
        else:
            reasoning = "Marginal impact on win rate"
        
        # Add synergy information
        synergy_value = ai.evaluate_card(card, player, upcoming_enemy, DeckState(draw_pile=current_deck), turn=1)
        
        results[card.name] = {
            "win_rate": win_rate,
            "avg_hp_remaining": avg_hp,
            "avg_turns": np.mean(card_turns),
            "delta_win_rate": delta_win,
            "delta_hp": delta_hp,
            "immediate_value": synergy_value,
            "recommendation": "Take" if delta_win > 0.02 else "Consider" if delta_win > 0 else "Skip",
            "reasoning": reasoning
        }
    
    return results


# Factory functions for different AI configurations
def create_greedy_ai() -> LookaheadAI:
    """Create AI that maximizes immediate damage."""
    return LookaheadAI(depth=0, samples=1, play_style=PlayStyle.GREEDY)


def create_defensive_ai() -> LookaheadAI:
    """Create AI that prioritizes survival."""
    return LookaheadAI(depth=1, samples=5, play_style=PlayStyle.DEFENSIVE)


def create_balanced_ai() -> LookaheadAI:
    """Create AI with balanced play style."""
    return LookaheadAI(depth=2, samples=10, play_style=PlayStyle.BALANCED)


def create_scaling_ai() -> LookaheadAI:
    """Create AI that prioritizes long-term scaling."""
    return LookaheadAI(depth=2, samples=10, play_style=PlayStyle.SCALING)
