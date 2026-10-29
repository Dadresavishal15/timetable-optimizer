"""
genetic_algorithm.py - Evolve timetables using DEAP

Representation:
    An individual is a list of (slot_index, room_index) tuples,
    one per session. The i-th gene maps session[i] to
    (slots[slot_index], rooms[room_index]).

Operators:
    Selection:  Tournament selection (k=3)
    Crossover:  Uniform crossover — swap genes independently with 50% chance
    Mutation:   Randomly reassign 1-2 sessions to new slot/room
    Elitism:    Preserve top N individuals across generations

Fitness:
    Minimise the penalty score from fitness.py (lower = better).
    DEAP uses weights=(-1.0,) for minimisation.
"""

import random
import time
from dataclasses import dataclass, field

from deap import base, creator, tools

from src.models import TimetableData, Assignment
from src.fitness import evaluate_fitness, FitnessWeights, FitnessBreakdown


# ─── GA Configuration ──────────────────────────────────────────────

@dataclass
class GAConfig:
    """All tuneable GA parameters in one place."""
    population_size: int = 100
    generations: int = 100
    crossover_prob: float = 0.7
    mutation_prob: float = 0.2
    tournament_size: int = 3
    elite_count: int = 5           # Best individuals preserved each generation
    early_stop_fitness: int = 0    # Stop if this penalty is reached
    random_seed: int | None = 42
    fitness_weights: FitnessWeights = field(default_factory=FitnessWeights)


@dataclass
class GAResult:
    """Result returned after the GA finishes."""
    best_assignments: list[Assignment]
    best_fitness: FitnessBreakdown
    generations_run: int
    fitness_log: list[dict]       # Per-generation stats
    runtime_seconds: float
    config: GAConfig

    def summary(self) -> str:
        lines = [
            "=" * 55,
            "GENETIC ALGORITHM RESULT",
            "=" * 55,
            f"Generations run:   {self.generations_run}",
            f"Runtime:           {self.runtime_seconds:.2f}s",
            f"Best penalty:      {self.best_fitness.total_penalty}",
            f"  Hard conflicts:  {self.best_fitness.hard_conflicts_count}",
            f"  Soft penalties:  {self.best_fitness.soft_penalty}",
            f"Population size:   {self.config.population_size}",
            f"Crossover prob:    {self.config.crossover_prob}",
            f"Mutation prob:     {self.config.mutation_prob}",
            "=" * 55,
        ]
        return "\n".join(lines)


# ─── DEAP Setup (module-level, created once) ───────────────────────

# Avoid re-creating DEAP classes if module is reloaded
if not hasattr(creator, "FitnessMin"):
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMin)


# ─── Core Functions ────────────────────────────────────────────────

def _create_individual(num_slots: int, num_rooms: int, num_sessions: int):
    """Create a random individual: list of (slot_idx, room_idx) tuples."""
    genes = []
    for _ in range(num_sessions):
        slot_idx = random.randint(0, num_slots - 1)
        room_idx = random.randint(0, num_rooms - 1)
        genes.append((slot_idx, room_idx))
    return creator.Individual(genes)


def _decode_individual(individual, data: TimetableData) -> list[Assignment]:
    """Convert a DEAP individual back into a list of Assignment objects."""
    assignments = []
    for i, (slot_idx, room_idx) in enumerate(individual):
        assignments.append(Assignment(
            session=data.sessions[i],
            slot=data.slots[slot_idx],
            room=data.rooms[room_idx],
        ))
    return assignments


def _evaluate(individual, data: TimetableData, weights: FitnessWeights):
    """DEAP-compatible fitness function. Returns a 1-tuple of penalty."""
    assignments = _decode_individual(individual, data)
    breakdown = evaluate_fitness(assignments, weights)
    return (breakdown.total_penalty,)


def _cx_uniform_timetable(ind1, ind2, indpb=0.5):
    """
    Uniform crossover: swap each gene independently with probability indpb.
    Operates in-place on both individuals.
    """
    for i in range(len(ind1)):
        if random.random() < indpb:
            ind1[i], ind2[i] = ind2[i], ind1[i]
    return ind1, ind2


def _mut_reassign(individual, num_slots: int, num_rooms: int, indpb=0.1):
    """
    Mutation: each gene has indpb chance of being reassigned to a
    random (slot, room) pair.
    """
    for i in range(len(individual)):
        if random.random() < indpb:
            individual[i] = (
                random.randint(0, num_slots - 1),
                random.randint(0, num_rooms - 1),
            )
    return (individual,)


# ─── Main GA Runner ────────────────────────────────────────────────

def run_genetic_algorithm(
    data: TimetableData,
    config: GAConfig | None = None,
) -> GAResult:
    """
    Run the Genetic Algorithm to find an optimal timetable.

    Args:
        data: TimetableData with sessions, slots, and rooms.
        config: Optional GA configuration (uses defaults if not provided).

    Returns:
        GAResult with the best timetable found and statistics.
    """
    if config is None:
        config = GAConfig()

    if config.random_seed is not None:
        random.seed(config.random_seed)

    num_slots = data.num_slots
    num_rooms = data.num_rooms
    num_sessions = data.num_sessions

    # ── DEAP Toolbox ────────────────────────────────────────────
    toolbox = base.Toolbox()
    toolbox.register("individual", _create_individual,
                     num_slots, num_rooms, num_sessions)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", _evaluate,
                     data=data, weights=config.fitness_weights)
    toolbox.register("select", tools.selTournament,
                     tournsize=config.tournament_size)
    toolbox.register("mate", _cx_uniform_timetable, indpb=0.5)
    toolbox.register("mutate", _mut_reassign,
                     num_slots=num_slots, num_rooms=num_rooms, indpb=0.1)

    # ── Initial population ──────────────────────────────────────
    population = toolbox.population(n=config.population_size)

    # Evaluate initial population
    for ind in population:
        ind.fitness.values = toolbox.evaluate(ind)

    fitness_log = []
    start_time = time.time()

    # ── Evolution loop ──────────────────────────────────────────
    for gen in range(config.generations):
        # Select elites
        elites = tools.selBest(population, config.elite_count)
        elites = [creator.Individual(e) for e in elites]  # deep copy

        # Selection
        offspring = toolbox.select(population, len(population) - config.elite_count)
        offspring = [creator.Individual(o) for o in offspring]  # deep copy

        # Crossover
        for i in range(0, len(offspring) - 1, 2):
            if random.random() < config.crossover_prob:
                toolbox.mate(offspring[i], offspring[i + 1])
                del offspring[i].fitness.values
                del offspring[i + 1].fitness.values

        # Mutation
        for i in range(len(offspring)):
            if random.random() < config.mutation_prob:
                toolbox.mutate(offspring[i])
                del offspring[i].fitness.values

        # Evaluate changed individuals
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid:
            ind.fitness.values = toolbox.evaluate(ind)

        # Re-evaluate elites (needed after deep copy)
        for e in elites:
            e.fitness.values = toolbox.evaluate(e)

        # Replace population
        population = elites + offspring

        # Log stats
        fits = [ind.fitness.values[0] for ind in population]
        best_fit = min(fits)
        avg_fit = sum(fits) / len(fits)
        worst_fit = max(fits)

        fitness_log.append({
            "generation": gen,
            "best": best_fit,
            "avg": round(avg_fit, 2),
            "worst": worst_fit,
        })

        # Early stopping
        if best_fit <= config.early_stop_fitness:
            break

    # ── Extract best solution ───────────────────────────────────
    best_individual = tools.selBest(population, 1)[0]
    best_assignments = _decode_individual(best_individual, data)
    best_breakdown = evaluate_fitness(best_assignments, config.fitness_weights)
    runtime = time.time() - start_time

    return GAResult(
        best_assignments=best_assignments,
        best_fitness=best_breakdown,
        generations_run=len(fitness_log),
        fitness_log=fitness_log,
        runtime_seconds=runtime,
        config=config,
    )


# ─── Quick test: run this file directly ─────────────────────────────
if __name__ == "__main__":
    from pathlib import Path
    from src.data_loader import load_from_json
    from src.validator import validate_timetable

    data_path = Path(__file__).parent.parent / "data" / "sample_data.json"
    data = load_from_json(data_path)
    print(data.summary())

    # Run GA with default config
    config = GAConfig(
        population_size=100,
        generations=100,
        random_seed=42,
    )
    print(f"\nRunning GA: pop={config.population_size}, gens={config.generations}...\n")

    result = run_genetic_algorithm(data, config)
    print(result.summary())

    # Show fitness progression (first 5, last 5)
    log = result.fitness_log
    print("\nFitness progression:")
    print(f"  {'Gen':>4s}  {'Best':>6s}  {'Avg':>8s}  {'Worst':>6s}")
    print(f"  {'-'*4}  {'-'*6}  {'-'*8}  {'-'*6}")
    show = log[:5] + [None] + log[-5:] if len(log) > 10 else log
    for entry in show:
        if entry is None:
            print(f"  {'...':>4s}")
        else:
            print(f"  {entry['generation']:4d}  {entry['best']:6.0f}  {entry['avg']:8.2f}  {entry['worst']:6.0f}")

    # Validate
    val = validate_timetable(result.best_assignments)
    print(f"\nValidation: {val.summary()}")

    # Show assignments
    print("\nBest timetable assignments:")
    for a in result.best_assignments:
        print(f"  {a}")
