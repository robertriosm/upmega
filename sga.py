"""
implementacion de SGA
"""

import json
import random

class sga:
    def __init__(self) -> None:
        pass

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