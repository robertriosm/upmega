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

        # self.semaphores = self.set_semaphores()
        # self.zone_map = self.set_zone_map()

    def gen_individual(self, value: str, score = 0): 
        """
        gens an empty dict individual 
        """
        return {'value': value, 'score': score}


    def gen_initial_population(self, N: int):
        """
        gens the initial population with a random value and score 0
        """
        return [self.gen_individual(''.join([random.choice(string.ascii_uppercase+' ') for _ in range(random.randint(0, 20))])) for _ in range(N)]


    def fitness(self, population: list[dict], goal_param: str):
        """
        quita puntos dependiendo de la longitud del individuo
        da puntos al individuo por cada caracter acertado
        da puntos al individuo por cada caracter posicionado acertado
        penaliza la distancia entre palabras
        esta normalizado entre (0,1)
        """

        for individual in population:
            a = 0 
            p = 0 
            Lw = len(goal_param)
            Lwi = len(individual["value"]) 
            longer, shorter = (individual["value"], goal_param) if len(individual["value"]) > len(goal_param) else (goal_param, individual["value"]) 
            Ls, Ll = len(shorter), len(longer)
            longer_1, longer_2 = longer[:Ls], longer[Ls:]

            for i in range(Ls):
                if shorter[i] == longer_1[i]:
                    a += 1
                    continue
                if shorter[i] in longer_1:
                    p += 1

            for c in longer_2:
                if c in shorter:
                    p += 1

            individual['score'] = (100*a + 20*p - 40*abs(Lw - Lwi)) / Lw # ya tiene un score, pero es mejor trabajarlo solo con positivos


        min_score = min(population, key=lambda i: i['score'])['score']
        # max_score = max(population, key=lambda i: i['score'])['score']

        for individual in population:
            individual['score'] = individual['score'] + abs(min_score) # positivos


    def select(self, population: list[dict], size: int): # TESTING
        """
        entrega una poblacion de un tamano para reproduccion
        debe ser mas elitista para ofrecer rapida convergencia (es busqueda, no optimizacion)
        """
        values = [individual['value'] for individual in population]
        scores = [individual['score'] for individual in population]

        mating_pool = []

        for _ in range(size):
            mating_pool.append(random.choices(values, weights=scores, k=2))
        
        return mating_pool 


    def crossover(self, mating_pool: list[list[str]]): # TESTING
        """
        how the mating pool creates new individuals from parents
        2 gens to pass: characters and length 
        parent1 and parent2 are string due to select's functionality and optimization
        """
        population = []

        for parent1, parent2 in mating_pool:
            Lp1, Lp2 = len(parent1), len(parent2)
            Lc = random.choice([Lp1, Lp2])
            value = ''
            score = 0

            for i in range(Lc):
                try:
                    c1 = parent1[i]
                except:
                    c1 = ''
                try:
                    c2 = parent2[i]
                except:
                    c2 = ''

                value += random.choice([c1, c2])

            population.append({"value": value, "score": score})

        return population 


    def inversion(self, individual: dict): # NEEDS TESTING!
        value = individual["value"]
        a, b = random.sample(range(len(value)), k=2).sort()
        individual["value"] = value[:a-1] + value[a:b-1:-1] + value[b:]


    def mutate(self, population: list[dict], p_char: float, p_len: float): # TESTING
        """
        population: the population dah
        p_char: the smaller, the less chances to mutate a char in the string
        p_len: the smaller, the less chances to mutate the length of the string
        """
        for individual in population:
            value = ""

            for c in individual["value"]:
                if random.random() <= p_char:
                    value += random.choice(string.ascii_uppercase)
                else:
                    value += c
            
                # esta parte no me gusta del todo pero por ahora saca el chance
                if random.random() <= p_len:
                    if random.random() > 0.5:
                        value += ''.join(random.choice([i for i in string.ascii_uppercase+' '])) 
                    else:
                        value = value[:-1]
            
            individual["value"] = value


    def convergence_criteria_met(self, population: list[dict], goal_param: str):
        """
        si un individuo ha alcanzado el objetivo, se detiene devuelve y se detiene el bucle
        """
        
        for individual in population:
            if individual["value"] == goal_param:
                return individual

        return False


    def sga(self, G: str, N: int, Np: int, generations: int):
        """
        G: goal
        N: initial population
        Np: mating pool size
        generations: iterations to do
        """

        population = self.gen_initial_population(N)

        for _ in range(generations):

            self.fitness(population, G)

            ccm = self.convergence_criteria_met(population, G)

            if ccm:
                return ccm

            mating_pool = self.select(population, Np)

            offspring = self.crossover(mating_pool)

            self.mutate(offspring, p_char=0.1, p_len=0.05)

            population = offspring

        return 'El SGA no pudo encontrar una solucion.'