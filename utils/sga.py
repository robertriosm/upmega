"""
implementacion de SGA
"""

import random

class sga:
    def __init__(self) -> None:
        # Configuracion inicial
        self.POPULATION = 5
        self.GENERATIONS = 500
        self.CROSSOVER_RATE = 0.4
        self.MUTATION_RATE = 0.2

        self.semaphores = self.set_semaphores()
        self.zone_map = self.set_zone_map()

    
    def fitness(self):
        pass

    def mutate(self):
        pass

    def crossover(self):
        pass

    def select(self):
        pass

    def generate(self):
        pass