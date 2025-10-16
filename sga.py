"""
implementacion de SGA con controlador
"""

import random
import numpy as np
import pygad as ga
from controller import Controller


class TlSga:
    def __init__(self, 
                 controller: Controller,
                 population = 5,
                 generations = 500,
                 crossover_rate = 0.4,
                 mutation_rate = 0.2,
                 mating_pool_size = 7,
                 solutions_per_population = 50
                 ) -> None:
        self._setup_config(population, generations, crossover_rate, mutation_rate, 
                         mating_pool_size, solutions_per_population)
        self._setup_controller(controller) 
        self._setup_ga()


    def _setup_config(self, population, generations, crossover_rate, mutation_rate, 
                    mating_pool_size, solutions_per_population): 
        # config 
        self.population = population
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate 
        self.mating_pool_size = mating_pool_size
        self.solutions_per_population = solutions_per_population
        self.number_of_genes = self.get_num_genes()
        # Metricas
        self.last_fitness = 0


    def _setup_controller(self, controller): 
        if not isinstance(controller, Controller):
            raise TypeError(
                f"controller debe ser una instancia de Controller, pero se recibió {type(controller).__name__}"
            )
        self.controller = controller
    

    def _setup_ga(self):
        self.ga_instance = ga.GA(num_generations=self.generations,
                                 num_parents_mating=self.mating_pool_size, 
                                 fitness_func=self.fitness,
                                 sol_per_pop=self.solutions_per_population, 
                                 num_genes=self.number_of_genes,
                                 on_generation=self.callback_generation)


    def run_simulation(self):
        self.controller.start_sumo_conn()
        self.controller.execute_simulation()
        self.controller.close_sumo_conn()
    

    def get_data():
        ...
    

    def get_num_genes(self):
        """
        el planteamiento es que un sistema de semaforos es un individuo, por lo tanto,
        un gen es una interseccion con semaforo
        """
        return self.controller.get_tl_id_count()
    

    def callback_generation(self): 
        print(f"Generation = {self.ga_instance.generations_completed}")
        print(f"Fitness    = {self.ga_instance.best_solution()[1]}")
        print(f"Change     = {self.ga_instance.best_solution()[1] - last_fitness}")
        last_fitness = self.ga_instance.best_solution()[1]


    def fitness(self):
        """
        F = w1T1 + w2T2 
        donde: w1, w2 son los pesos y T1, T2 son tiempo en cola y tiempo de viaje
        """
        w1 = 0.8
        w2 = 0.7

        T1 = ...
        T2 = ...

        F = ...

        return min(F)


    def execute(self, N: int, Np: int, generations: int):
        """
        N: initial population
        Np: mating pool size
        generations: iterations to do
        """

        population = self.gen_initial_population(N)

        for _ in range(generations):
            self.fitness(population)
            ccm = self.convergence_criteria_met(population, G)

            if ccm:
                return ccm

            mating_pool = self.select(population, Np)
            offspring = self.crossover(mating_pool)
            self.mutate(offspring, p_char=0.1, p_len=0.05)
            population = offspring

        return 'El SGA no pudo encontrar una solucion.'