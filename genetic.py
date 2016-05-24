import array, random
import numpy as np
from deap import creator, base, tools, algorithms
from network import Network

IND_SIZE = 14


creator.create('FitnessMax', base.Fitness, weights=(1., ))
creator.create("Individual", list, typecode='b', fitness=creator.FitnessMax)

toolbox = base.Toolbox()

toolbox.register("attr_float", random.random)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=IND_SIZE)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def evalOneMax(individual):
    n = Network(4, 2, 5)
    n.N_CONTENTS = 3 * 10 ** 4
    n.N_WARMUP_REQUESTS = 4 * 10 ** 4
    n.N_MEASURED_REQUESTS = 1 * 10 ** 4
    n.GAMMA = 1
    n.ALPHA = .8

    n.INTERNAL_COST = 2
    n.EXTERNAL_COST = 10

    n.on_path = True
    n.ind = individual

    n.run()

    return n.hits,


toolbox.register("evaluate", evalOneMax)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

population = toolbox.population(n=10)

NGEN=40
for gen in range(NGEN):
    print gen
    offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.1)
    fits = toolbox.map(toolbox.evaluate, offspring)
    for fit, ind in zip(fits, offspring):
        ind.fitness.values = fit
    population = offspring
    