# virus_sim_game

## Safety First
This repository contains a **fictional, educational simulation**. The so-called
"virus" is just a game character. It never touches real files, processes, or
networks. The program runs entirely in memory and exists to help learners think
about defensive strategies in a playful context.

## Project Overview
`virus_sim_game` is a turn-based terminal simulation written in Python 3 using
only the standard library. The world includes three main actor types:

- **Processes** – friendly software characters that can be temporarily
  compromised in the simulation.
- **Virus** – the player-controlled game entity with four abilities: camouflage,
  replicator, adapt, and mirror. Each ability is represented as a harmless game
  mechanic (e.g., camouflage reduces the chance of detection).
- **Antivirus agents** – defenders that scan for the virus and repair
  compromised processes.

All of the logic lives in four modules:

| File | Purpose |
| ---- | ------- |
| `entities.py` | Defines the `Process`, `Virus`, `Antivirus`, and `World` classes. |
| `scenarios.py` | Provides preset scenarios and deterministic showcase runs. |
| `simulate.py` | Command-line interface for running simulations. |
| `README.md` | Project documentation (this file). |

## Getting Started
1. Ensure Python 3.8+ is installed.
2. Clone or download this repository.
3. From the project directory run one of the scenarios:

```bash
python simulate.py --scenario basic --turns 20
```

The `--turns` flag controls how many rounds to simulate, `--seed` can lock in a
random seed, and `--no-explanation` hides the ability explanation text if you
want a shorter log.

### Game Ability Guide
The program also prints this explanation by default to help newcomers map the
abilities to familiar videogame mechanics:

- **Camouflage** – like equipping a stealth cloak; scanners have a harder time
  seeing the virus, but it is never invisible.
- **Replicator** – similar to summoning allies; the virus can spawn extra clones
  that obey the same rules.
- **Adapt** – comparable to leveling up a defense skill after dodging attacks;
  each missed scan makes the virus slightly harder to catch.
- **Mirror** – reminiscent of a shapeshifter that mimics other characters to
  confuse opponents and reduce detection odds.

## Deterministic Showcase Runs
To highlight how each ability influences outcomes, run the showcase mode:

```bash
python simulate.py --showcase
```

This produces unit-test-like deterministic summaries using fixed random seeds.
Each block reports the same results on every machine, making it easy to compare
ability combinations.

## Example Output (100 turns)
Below is trimmed output from running the basic scenario for 100 turns. The
random seed is locked so you can reproduce the same events:

```bash
python simulate.py --scenario basic --turns 100 --seed 2024
```

<details>
<summary>Sample log</summary>

```
Game Ability Guide:
  Camouflage  -> Like a stealth cloak in an adventure game: it makes the
                   virus harder to spot, but not invisible.
  Replicator  -> Similar to summoning companions in a strategy game: the
                   virus can spawn extra copies that follow the same rules.
  Adapt       -> Comparable to leveling up after dodging attacks; each
                   failed scan gives a small defensive boost.
  Mirror      -> Think of a shapeshifter class that imitates others to
                   confuse enemies, lowering the odds of detection.

-- Turn 1 --
Edu-Virus compromised Spreadsheet (chance 0.39).
ShieldOne scanned Edu-Virus but missed (roll 0.89 vs 0.33).
-- Turn 2 --
Edu-Virus failed to compromise PhotoOrganizer (chance 0.43).
ShieldOne scanned Edu-Virus but missed (roll 0.35 vs 0.31).
-- Turn 3 --
Edu-Virus compromised MusicPlayer (chance 0.40).
ShieldOne scanned Edu-Virus but missed (roll 0.73 vs 0.30).
-- Turn 4 --
Edu-Virus failed to compromise PhotoOrganizer (chance 0.43).
ShieldOne scanned Edu-Virus but missed (roll 0.53 vs 0.28).
-- Turn 5 --
Edu-Virus failed to compromise NoteTaker (chance 0.37).
Edu-Virus replicated into Edu-Virus-clone-1.
ShieldOne scanned Edu-Virus but missed (roll 0.76 vs 0.26).
...
-- Turn 100 --
NoteTaker stabilized itself.
Edu-Virus-clone-4 compromised NoteTaker (chance 0.38).
ShieldOne scanned Edu-Virus-clone-13 but missed (roll 0.59 vs 0.19).
ShieldOne repaired PhotoOrganizer.
Simulation Summary:
  Turns simulated: 100
  Processes compromised: 4/5
  Active viruses: 11
  Neutralized viruses: 29
  Total clone events: 39
```

</details>

## Educational Goals
- Demonstrate how probabilistic game mechanics can mirror cybersecurity ideas
  without touching real systems.
- Encourage experimentation with different ability combinations to see how
  defenders and attackers can reach equilibrium.
- Provide a safe sandbox for classroom activities or self-paced learning.

Have fun exploring the simulation, and remember: everything here is make-believe
and absolutely safe to run locally.
