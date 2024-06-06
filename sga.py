"""
implementacion de SGA
"""

import json
import random

class sga:
    def __init__(self) -> None:
        # Configuracion inicial
        self.POPULATION = 5
        self.GENERATIONS = 500
        self.CROSSOVER_RATE = 0.4
        self.MUTATION_RATE = 0.2

        # 
        self.semaphores = semaphores
        self.zone_map = zone_map



    def get_semaphores(n, name):
        semaforos = []
        for i in range(n):
            semaforo = {
                'id': i,
                'tiempo_verde': random.randint(1, 60),  # tiempo en segundos
                'tiempo_rojo': random.randint(1, 60),  # tiempo en segundos
            }
            semaforos.append(semaforo)
        
        with open(f'{name}.json', 'w') as f:
            json.dump(semaforos, f, indent=4)
    
    def fitness(self):
        pass

    def mutate(self):
        pass

    def crossover(self):
        pass

    def select(self):
        pass

    def execute(self):
        pass