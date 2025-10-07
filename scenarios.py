"""Preset scenarios for the virus simulation game.

Every scenario is deterministic when provided with the same random seed and
only uses the classes defined in :mod:`entities`. The scenarios demonstrate
how different ability combinations play out purely as game mechanics.
"""
from __future__ import annotations

import random
from typing import Callable, Dict, List, Tuple

from entities import Antivirus, Process, Virus, World

# Type alias for scenario builders. Builders accept an optional seed.
ScenarioBuilder = Callable[..., World]


def _build_world(
    *,
    rng_seed: int,
    virus: Virus,
    antivirus: List[Antivirus],
    processes: List[Process],
) -> World:
    """Helper that wires the world together using a deterministic seed."""

    rng = random.Random(rng_seed)
    return World(processes=processes, antivirus_agents=antivirus, viruses=[virus], rng=rng)


def basic_scenario(seed: int = 42) -> World:
    """A gentle starting scenario for demonstrations."""

    processes = [
        Process("DrawingApp", stability=0.9),
        Process("MusicPlayer", stability=0.8),
        Process("PhotoOrganizer", stability=0.7),
        Process("Spreadsheet", stability=0.85),
        Process("NoteTaker", stability=0.95),
    ]
    virus = Virus(
        "Edu-Virus",
        camouflage=True,
        replicator=True,
        adapt=True,
        mirror=False,
    )
    antivirus = [Antivirus("ShieldOne", detection_rate=0.55, repair_rate=0.25)]
    return _build_world(rng_seed=seed, virus=virus, antivirus=antivirus, processes=processes)


def stealth_showcase(seed: int = 7) -> World:
    """Showcase high stealth and mimicry versus rapid antivirus scans."""

    processes = [
        Process("ChatApp", stability=0.8),
        Process("Calendar", stability=0.85),
        Process("ArcadeGame", stability=0.75),
        Process("PhotoEditor", stability=0.7),
    ]
    virus = Virus("Shadow", camouflage=True, replicator=False, adapt=True, mirror=True)
    antivirus = [
        Antivirus("Watcher", detection_rate=0.65, repair_rate=0.3),
        Antivirus("Guardian", detection_rate=0.5, repair_rate=0.2),
    ]
    return _build_world(rng_seed=seed, virus=virus, antivirus=antivirus, processes=processes)


def replication_showcase(seed: int = 99) -> World:
    """Show how replication increases pressure on the defenders."""

    processes = [
        Process("Mail", stability=0.9),
        Process("Presentation", stability=0.75),
        Process("IDE", stability=0.8),
        Process("ImageViewer", stability=0.85),
        Process("Browser", stability=0.7),
        Process("GameLauncher", stability=0.65),
    ]
    virus = Virus("Hydra", camouflage=False, replicator=True, adapt=False, mirror=False)
    antivirus = [
        Antivirus("RapidScan", detection_rate=0.6, repair_rate=0.35),
    ]
    return _build_world(rng_seed=seed, virus=virus, antivirus=antivirus, processes=processes)


SCENARIOS: Dict[str, ScenarioBuilder] = {
    "basic": basic_scenario,
    "stealth": stealth_showcase,
    "replication": replication_showcase,
}


def showcase_runs() -> List[Tuple[str, str, str]]:
    """Return deterministic summaries for different ability combinations."""

    cases = [
        (
            "Camouflage + Adapt",
            Virus("StudyCase-Stealth", camouflage=True, adapt=True, replicator=False, mirror=False),
            [Antivirus("Analyst", detection_rate=0.5, repair_rate=0.2)],
            [
                Process("Writer", stability=0.9),
                Process("Painter", stability=0.85),
                Process("Composer", stability=0.8),
            ],
            15,
            13,
        ),
        (
            "Replicator only",
            Virus("StudyCase-Rep", camouflage=False, adapt=False, replicator=True, mirror=False),
            [Antivirus("Responder", detection_rate=0.55, repair_rate=0.25)],
            [
                Process("Planner", stability=0.9),
                Process("Editor", stability=0.8),
                Process("Sketch", stability=0.7),
                Process("Rhythm", stability=0.75),
            ],
            12,
            21,
        ),
        (
            "Mirror + Camouflage",
            Virus("StudyCase-Mirror", camouflage=True, adapt=False, replicator=False, mirror=True),
            [Antivirus("Observer", detection_rate=0.65, repair_rate=0.3)],
            [
                Process("MailClient", stability=0.9),
                Process("VideoCall", stability=0.85),
                Process("PuzzleGame", stability=0.8),
            ],
            10,
            9,
        ),
    ]

    summaries: List[Tuple[str, str, str]] = []
    for label, virus, av, processes, seed, turns in cases:
        world = _build_world(rng_seed=seed, virus=virus, antivirus=av, processes=processes)
        world.run(turns)
        summaries.append((label, world.summary(), World.game_explanation()))
    return summaries

