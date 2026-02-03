#!/usr/bin/env python3
"""
Example usage of the Monte Carlo Simulation Engine and Deck Evaluation system.

This script demonstrates:
1. Running Monte Carlo simulations
2. Evaluating deck compositions
3. Generating documentation
4. Verifying data
"""

from pathlib import Path
from src.simulation.simulator import MonteCarloSimulator
from src.models.card import Card, CardType, Rarity
from src.models.relic import Relic, RelicRarity
from src.models.deck import DeckEvaluation
from src.docs.generator import generate_documentation
from src.verification.verifier import verify_data


def example_monte_carlo_simulation():
    """Run a small Monte Carlo simulation."""
    print("=" * 60)
    print("MONTE CARLO SIMULATION EXAMPLE")
    print("=" * 60)
    
    # Initialize simulator
    simulator = MonteCarloSimulator(
        root_seed=20260202,
        iterations=100,  # Small number for demo
        character="Ironclad"
    )
    
    # Run BASE scenario
    print("\nRunning BASE scenario...")
    base_results = simulator.run_base_scenario()
    print(f"  Win rate: {base_results['win_rate']:.2f}%")
    print(f"  Median turns: {base_results['median_turns']:.1f}")
    print(f"  Total runs: {base_results['total_runs']}")
    
    # Run COMPLEX scenario
    print("\nRunning COMPLEX scenario...")
    complex_results = simulator.run_complex_scenario()
    print(f"  Win rate: {complex_results['win_rate']:.2f}%")
    print(f"  Median turns: {complex_results['median_turns']:.1f}")
    
    # Compare scenarios
    print("\nRunning all scenarios for comparison...")
    all_results = simulator.run_all_scenarios()
    comparison = MonteCarloSimulator.compare_scenarios(all_results)
    
    print(f"\nScenario Comparison:")
    print(f"  Best scenario (win rate): {comparison['best_scenario']}")
    print(f"  Win rates:")
    for scenario, wr in comparison["win_rates"].items():
        print(f"    {scenario}: {wr:.2f}%")
    
    return all_results


def example_deck_evaluation():
    """Evaluate a deck using the composite scoring system."""
    print("\n" + "=" * 60)
    print("DECK EVALUATION EXAMPLE")
    print("=" * 60)
    
    # Build a strength-scaling deck
    cards = [
        Card("Heavy Blade", CardType.ATTACK, 2, Rarity.COMMON, 
             tier_score=95.0, fusion_tags=["Strength-scaling"]),
        Card("Heavy Blade", CardType.ATTACK, 2, Rarity.COMMON, 
             tier_score=95.0, fusion_tags=["Strength-scaling"]),
        Card("Demon Form", CardType.POWER, 3, Rarity.RARE, 
             tier_score=92.0, fusion_tags=["Strength-scaling"]),
        Card("Limit Break", CardType.SKILL, 1, Rarity.RARE, 
             tier_score=88.0, fusion_tags=["Strength-scaling"]),
        Card("Inflame", CardType.POWER, 1, Rarity.UNCOMMON, 
             tier_score=75.0, fusion_tags=["Strength-scaling"]),
        Card("Inflame", CardType.POWER, 1, Rarity.UNCOMMON, 
             tier_score=75.0, fusion_tags=["Strength-scaling"]),
        Card("Bash", CardType.ATTACK, 2, Rarity.COMMON, 
             tier_score=85.0, function_tags=["Damage", "Vulnerable"]),
        Card("Strike", CardType.ATTACK, 1, Rarity.BASIC, tier_score=50.0),
        Card("Strike", CardType.ATTACK, 1, Rarity.BASIC, tier_score=50.0),
        Card("Strike", CardType.ATTACK, 1, Rarity.BASIC, tier_score=50.0),
        Card("Defend", CardType.SKILL, 1, Rarity.BASIC, tier_score=55.0),
        Card("Defend", CardType.SKILL, 1, Rarity.BASIC, tier_score=55.0),
        Card("Defend", CardType.SKILL, 1, Rarity.BASIC, tier_score=55.0),
    ]
    
    relics = [
        Relic("Burning Blood", RelicRarity.STARTER, "Heal 6 HP after combat", tier_score=60.0),
        Relic("Vajra", RelicRarity.BOSS, "Gain 1 Strength at start of combat", 
              synergies=["Strength-scaling"], tier_score=85.0),
    ]
    
    # Evaluate the deck
    deck = DeckEvaluation(
        cards=cards, 
        relics=relics,
        name="Strength Scaling Demo",
        character="Ironclad"
    )
    
    breakdown = deck.get_breakdown()
    
    print(f"\nDeck: {deck.name}")
    print(f"  Size: {breakdown['deck_size']} cards, {breakdown['relic_count']} relics")
    print(f"\nComposite Score Breakdown:")
    print(f"  Card Quality (Q):      {breakdown['card_quality']:.1f}")
    print(f"  Synergy Coherence (S): {breakdown['synergy_coherence']:.1f}")
    print(f"  Curve Smoothness (C):  {breakdown['curve_smoothness']:.1f}")
    print(f"  Consistency (K):       {breakdown['consistency']:.1f}")
    print(f"  Relic Impact (R):      {breakdown['relic_impact']:.1f}")
    print(f"\n  Overall Score: {breakdown['overall_score']:.1f}/100")
    
    return deck


def example_data_verification():
    """Run data verification checks."""
    print("\n" + "=" * 60)
    print("DATA VERIFICATION EXAMPLE")
    print("=" * 60)
    
    # Verify all data
    report = verify_data()
    
    print(f"\nVerification Results:")
    print(f"  Verified items: {report['verified_count']}")
    print(f"  Errors: {report['error_count']}")
    print(f"  Warnings: {report['warning_count']}")
    print(f"  Status: {'✓ PASSED' if report['passed'] else '✗ FAILED'}")
    
    if report['error_count'] > 0:
        print(f"\n  First few errors:")
        for error in report['errors'][:3]:
            print(f"    - {error['item_name']}: {error['description']}")
    
    return report


def example_documentation_generation(simulation_results):
    """Generate documentation from simulation results."""
    print("\n" + "=" * 60)
    print("DOCUMENTATION GENERATION EXAMPLE")
    print("=" * 60)
    
    # Prepare results in expected format
    doc_results = {
        "scenarios": simulation_results
    }
    
    # Generate documentation
    output_dir = Path("./example_outputs")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\nGenerating documentation in {output_dir}...")
    
    try:
        outputs = generate_documentation(
            simulation_results=doc_results,
            output_dir=output_dir
        )
        
        print(f"\nGenerated files:")
        for fmt, path in outputs.items():
            print(f"  {fmt.upper()}: {path}")
        
        return outputs
    except Exception as e:
        print(f"  Note: {e}")
        print("  (Documentation generation requires results with proper structure)")
        return None


def main():
    """Run all examples."""
    print("\n" + "#" * 60)
    print("#  MONTE CARLO SIMULATION ENGINE DEMO")
    print("#" * 60 + "\n")
    
    # 1. Monte Carlo Simulation
    simulation_results = example_monte_carlo_simulation()
    
    # 2. Deck Evaluation
    deck = example_deck_evaluation()
    
    # 3. Data Verification
    verification_report = example_data_verification()
    
    # 4. Documentation Generation
    docs = example_documentation_generation(simulation_results)
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nAll components have been demonstrated.")
    print("See the README.md for more detailed usage examples.")
    print()


if __name__ == "__main__":
    main()
