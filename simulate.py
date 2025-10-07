"""Command line interface for the virus simulation game.

This runner keeps everything offline and purely illustrative. It never
interacts with the real filesystem, network, or system processes. The
"virus" is just a playful game character designed for educational purposes.
"""
from __future__ import annotations

import argparse
from typing import Optional

from entities import World
from scenarios import SCENARIOS, showcase_runs


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the simulation."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the virus simulation game. The simulation is safe and purely "
            "educational, modelling imaginary software components."
        )
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS.keys()),
        default="basic",
        help="Which preset scenario to run.",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=50,
        help="Number of turns to simulate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed to make the run deterministic.",
    )
    parser.add_argument(
        "--showcase",
        action="store_true",
        help=(
            "Run deterministic showcase simulations that highlight the"
            " different virus abilities."
        ),
    )
    parser.add_argument(
        "--no-explanation",
        action="store_true",
        help="Skip printing the ability explanation text.",
    )
    return parser.parse_args()


def build_world(name: str, seed: Optional[int]) -> World:
    """Construct a world instance for the selected scenario."""

    builder = SCENARIOS[name]
    if seed is None:
        return builder()  # type: ignore[misc]
    return builder(seed)


def run_world(world: World, turns: int, *, print_events: bool = True) -> None:
    """Advance the world a number of turns, optionally printing events."""

    for _ in range(turns):
        events = world.step()
        if print_events:
            for entry in events:
                print(entry)
    print(world.summary())


def run_showcase() -> None:
    """Execute deterministic runs that act like unit tests for abilities."""

    print("Running ability showcase (deterministic seeds)...")
    for label, summary, explanation in showcase_runs():
        print(f"== {label} ==")
        print(summary.strip())
        print(explanation.strip())
        print()


def main() -> None:
    args = parse_args()

    if args.showcase:
        run_showcase()
        return

    world = build_world(args.scenario, args.seed)

    if not args.no_explanation:
        print(World.game_explanation().strip())
        print()

    run_world(world, args.turns, print_events=True)


if __name__ == "__main__":
    main()

