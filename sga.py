"""
implementacion de SGA con controlador
"""

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
    

    def get_num_genes(self):
        """
        el planteamiento es que un sistema de semaforos es un individuo, por lo tanto,
        un gen es una interseccion con semaforo
        """
        return self.controller.get_tl_id_count()


    def get_tl_ids(self):
        return self.controller.get_tl_ids()
    

    def callback_generation(self): 
        print(f"Generation = {self.ga_instance.generations_completed}")
        print(f"Fitness    = {self.ga_instance.best_solution()[1]}")
        print(f"Change     = {self.ga_instance.best_solution()[1] - last_fitness}")
        last_fitness = self.ga_instance.best_solution()[1]
    

    def get_avg_waiting_time(self, data):
        return np.sum(np.array(data)) / len(data)


    def get_avg_travel_time(self, data): 
        return np.sum(np.array(data)) / len(data)


    def apply_solution(self, solution): 
        """
        aplicar configuracion de semaforos encontrada por algoritmo a la network  
        """
        phase_counts = []

        for tl_id in self.get:
            logic = self.controller.get_tl_logic(tl_id)
            phase_counts.append(len(logic.phases))

        offsets = np.cumsum([0] + phase_counts)

        for i, tl_id in enumerate(self.get):
            start, end = offsets[i], offsets[i+1]
            durations = solution[start:end]

            logic = self.controller.get_tl_logic(tl_id)
            new_phases = []

            for j, phase in enumerate(logic.phases):
                new_phases.append(self.controller.phase(phase, durations[j]))

            new_logic = self.controller.logic(logic, new_phases)
            self.controller.set_tl_logic(tl_id, new_logic)


    def fitness(self, solution, solution_idx):
        """
        solution: cada configuracion de semaforos a evaluar
        solution_idx: el id de la config

        F = w1T1 + w2T2 
        donde: w1, w2 son los pesos y T1, T2 son tiempo en cola y tiempo de viaje
        """
        self.apply_solution(solution)

        w1 = 0.8
        w2 = 0.7

        veh_wt, veh_tt = self.controller.execute_simulation()

        T1 = self.get_avg_waiting_time(veh_wt)
        T2 = self.get_avg_travel_time(veh_tt)

        F = w1*T1 + w2*T2

        fitness = 1.0 / F

        return fitness


    def execute(self):
        """
        N: initial population
        Np: mating pool size
        generations: iterations to do
        """
        self.ga_instance.run()
