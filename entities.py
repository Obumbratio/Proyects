"""Entity definitions for the educational virus simulation game.

This module intentionally models a harmless, fully-contained simulation
where a fictional "virus" interacts with equally fictional processes and
antivirus agents. The goal is to teach systems thinking without touching
real files, networks, or operating system resources.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import random


@dataclass
class Process:
    """Represents a normal process running inside the simulated world."""

    name: str
    stability: float = 1.0
    compromised: bool = False

    def step(self, rng: random.Random) -> Optional[str]:
        """Allow the process to self-heal over time.

        Parameters
        ----------
        rng:
            Random number generator used to keep the simulation deterministic
            when required.

        Returns
        -------
        Optional[str]
            A textual event description when the process heals, otherwise
            ``None``.
        """

        if self.compromised and rng.random() < (0.05 * self.stability):
            self.compromised = False
            return f"{self.name} stabilized itself."
        return None


@dataclass
class Virus:
    """Fictional virus entity used strictly within the simulated world.

    Each ability is implemented as a game mechanic:
    - ``camouflage`` lowers the probability of being detected.
    - ``replicator`` allows the virus to spawn harmless clones in the
      simulation.
    - ``adapt`` increases resistance to detection after failed scans.
    - ``mirror`` lets the virus visually imitate another process name.
    """

    name: str
    camouflage: bool = False
    replicator: bool = False
    adapt: bool = False
    mirror: bool = False
    active: bool = True
    mimicked_name: Optional[str] = None
    adaptation_bonus: float = 0.0
    clones_created: int = 0
    origin_name: str = field(default="", init=False)

    def __post_init__(self) -> None:
        """Initialize the origin name used for clone naming."""

        if not self.origin_name:
            self.origin_name = self.name

    def detection_difficulty(self) -> float:
        """Return a multiplicative factor applied to antivirus detection.

        Lower values make the virus harder to detect. The value never drops
        below 0.2 to keep the game balanced.
        """

        factor = 1.0
        if self.camouflage:
            factor *= 0.6
        if self.mirror and self.mimicked_name:
            factor *= 0.75
        factor *= max(0.2, 1.0 - self.adaptation_bonus)
        return max(0.2, factor)

    def on_detection_attempt(self, success: bool) -> None:
        """Update adaptation bonus depending on detection results."""

        if not self.adapt:
            return
        if success:
            # Reset adaptation when caught to demonstrate learning resets.
            self.adaptation_bonus = 0.0
        else:
            self.adaptation_bonus = min(0.5, self.adaptation_bonus + 0.05)

    def create_clone(self, clone_id: int) -> "Virus":
        """Return a new virus instance representing a clone."""

        clone = Virus(
            name=f"{self.origin_name}-clone-{clone_id}",
            camouflage=self.camouflage,
            replicator=self.replicator,
            adapt=self.adapt,
            mirror=self.mirror,
        )
        clone.adaptation_bonus = self.adaptation_bonus * 0.5
        clone.mimicked_name = self.mimicked_name
        clone.origin_name = self.origin_name
        return clone

    def step(self, world: "World", rng: random.Random) -> List[str]:
        """Simulate the virus for a single turn.

        The virus targets processes, optionally clones itself, and records
        textual events for the turn. All actions are purely informational.
        """

        if not self.active:
            return []

        events: List[str] = []
        healthy_processes = [p for p in world.processes if not p.compromised]
        if healthy_processes:
            target = rng.choice(healthy_processes)
            infection_chance = 0.35 + 0.25 * (1.0 - target.stability)
            if self.adapt:
                infection_chance += 0.05 * self.adaptation_bonus
            infection_chance = min(0.9, infection_chance)

            if self.mirror:
                # Remember the visual disguise for storytelling purposes.
                self.mimicked_name = target.name

            if rng.random() < infection_chance:
                target.compromised = True
                events.append(
                    f"{self.name} compromised {target.name} (chance {infection_chance:.2f})."
                )
            else:
                events.append(
                    f"{self.name} failed to compromise {target.name} (chance {infection_chance:.2f})."
                )

        if self.replicator and rng.random() < 0.25:
            clone_id = world.next_clone_id()
            clone = self.create_clone(clone_id)
            if world.schedule_new_virus(clone):
                self.clones_created += 1
                events.append(f"{self.name} replicated into {clone.name}.")

        return events


@dataclass
class Antivirus:
    """Antivirus agent that scans for simulated viruses."""

    name: str
    detection_rate: float = 0.5
    repair_rate: float = 0.2

    def step(self, world: "World", rng: random.Random) -> List[str]:
        """Perform scanning and optional repairs."""

        events: List[str] = []
        active_viruses = [v for v in world.viruses if v.active]
        if active_viruses:
            target = rng.choice(active_viruses)
            detection_chance = max(0.05, self.detection_rate * target.detection_difficulty())
            roll = rng.random()
            if roll < detection_chance:
                target.active = False
                target.on_detection_attempt(success=True)
                events.append(
                    f"{self.name} neutralized {target.name} (chance {detection_chance:.2f})."
                )
            else:
                target.on_detection_attempt(success=False)
                events.append(
                    f"{self.name} scanned {target.name} but missed (roll {roll:.2f} vs {detection_chance:.2f})."
                )

        compromised = [p for p in world.processes if p.compromised]
        if compromised and rng.random() < self.repair_rate:
            repaired = rng.choice(compromised)
            repaired.compromised = False
            events.append(f"{self.name} repaired {repaired.name}.")

        return events


class World:
    """Self-contained world that drives the simulation turn by turn."""

    def __init__(
        self,
        processes: List[Process],
        antivirus_agents: List[Antivirus],
        viruses: List[Virus],
        *,
        rng: Optional[random.Random] = None,
        max_viruses: int = 40,
    ) -> None:
        self.processes = processes
        self.antivirus_agents = antivirus_agents
        self.viruses = viruses
        self.turn = 0
        self._rng = rng or random.Random()
        self._event_log: List[List[str]] = []
        self._pending_viruses: List[Virus] = []
        self._clone_counter = 0
        self.max_viruses = max_viruses

    @property
    def rng(self) -> random.Random:
        """Expose the random number generator for deterministic seeds."""

        return self._rng

    def next_clone_id(self) -> int:
        """Return a unique identifier for clones."""

        self._clone_counter += 1
        return self._clone_counter

    def schedule_new_virus(self, virus: Virus) -> bool:
        """Queue a new virus to be added after the current turn.

        Returns ``True`` when the clone is accepted. If the maximum number of
        viruses is already reached the clone is skipped and ``False`` is
        returned. This keeps the output readable.
        """

        if len(self.viruses) + len(self._pending_viruses) >= self.max_viruses:
            # Provide a soft cap so the simulation stays readable and fast.
            return False
        self._pending_viruses.append(virus)
        return True

    def step(self) -> List[str]:
        """Advance the simulation by a single turn."""

        self.turn += 1
        turn_events: List[str] = [f"-- Turn {self.turn} --"]

        # Processes may recover on their own.
        for process in self.processes:
            event = process.step(self._rng)
            if event:
                turn_events.append(event)

        # Viruses act next.
        for virus in list(self.viruses):
            turn_events.extend(virus.step(self, self._rng))

        # Apply scheduled viruses.
        if self._pending_viruses:
            self.viruses.extend(self._pending_viruses)
            self._pending_viruses = []

        # Antivirus agents respond last.
        for agent in self.antivirus_agents:
            turn_events.extend(agent.step(self, self._rng))

        self._event_log.append(turn_events)
        return turn_events

    def run(self, turns: int) -> None:
        """Run the simulation for ``turns`` iterations."""

        for _ in range(turns):
            self.step()

    def summary(self) -> str:
        """Return a human-readable summary of the world state."""

        total_processes = len(self.processes)
        compromised = sum(1 for p in self.processes if p.compromised)
        inactive = sum(1 for v in self.viruses if not v.active)
        active = sum(1 for v in self.viruses if v.active)
        clones = sum(v.clones_created for v in self.viruses)
        return (
            "Simulation Summary:\n"
            f"  Turns simulated: {self.turn}\n"
            f"  Processes compromised: {compromised}/{total_processes}\n"
            f"  Active viruses: {active}\n"
            f"  Neutralized viruses: {inactive}\n"
            f"  Total clone events: {clones}\n"
        )

    def event_log(self) -> List[List[str]]:
        """Return all events recorded per turn."""

        return list(self._event_log)

    @staticmethod
    def game_explanation() -> str:
        """Explain abilities using friendly videogame analogies."""

        return (
            "Game Ability Guide:\n"
            "  Camouflage  -> Like a stealth cloak in an adventure game: it makes the\n"
            "                   virus harder to spot, but not invisible.\n"
            "  Replicator  -> Similar to summoning companions in a strategy game: the\n"
            "                   virus can spawn extra copies that follow the same rules.\n"
            "  Adapt       -> Comparable to leveling up after dodging attacks; each\n"
            "                   failed scan gives a small defensive boost.\n"
            "  Mirror      -> Think of a shapeshifter class that imitates others to\n"
            "                   confuse enemies, lowering the odds of detection.\n"
        )

