"""
implementacion de SGA con controlador
"""

import numpy as np
import pygad as ga
from controller import Controller


class TlSga:
    def __init__(self, 
                 controller: Controller,
                 population = 20,
                 generations = 300,
                 mating_pool_size = 8,
                 crossover_type = "single_point",
                 mutation_type = "random",
                 selection_type = "sss",
                 mutation_probability = 0.1
                 ) -> None:
        self._setup_controller(controller) 
        self._setup_config(population, generations, crossover_type, 
                           mutation_type, mating_pool_size, selection_type, mutation_probability)
        self._setup_ga()


    def _setup_config(self, population, generations, crossover_type, 
                      mutation_type, mating_pool_size, selection_type, mutation_probability): 
        """
        inicializar parametros del GA
        """
        self.population = population
        self.generations = generations
        self.crossover_type = crossover_type
        self.mutation_type = mutation_type 
        self.mating_pool_size = mating_pool_size
        self.selection_type = selection_type
        self.mutation_probability = mutation_probability
        self.last_fitness = 0
        self.sid = 0


    def _setup_controller(self, controller): 
        """
        inicializar controlador
        """
        if not isinstance(controller, Controller):
            raise TypeError(
                f"controller debe ser una instancia de Controller, se recibió {type(controller).__name__}"
            )
        self.controller = controller
    

    def _setup_ga(self):
        """
        inicializar y configurar el GA
        """

        def fitness(solution, tls_ids, offsets):
            """
            F = w1T1 + w2T2 
            donde: w1, w2 son los pesos y T1, T2 son tiempo en cola y tiempo de viaje
            """
            net_path = self.controller.apply_solution(solution, self.sid, tls_ids, offsets)
            durations, waiting_times = self.controller.execute_simulation(self.sid, net_path)
            self.sid += 1 # aumentar como id unico

            T1 = np.mean(np.array(durations, dtype=np.float16))
            T2 = np.mean(np.array(waiting_times, dtype=np.float16))
            w1 = 1
            w2 = 1

            F = w1*T1 + w2*T2 
            fitness = 1.0 / (F + 1e-6) 

            return fitness 
        

        base_genome, phase_counts = self.controller.build_genome()
        offsets = np.cumsum([0] + phase_counts)
        tls_ids = self.controller.get_tl_ids() # garantizar que siempre se pasa la misma lista 

        fitness_func = lambda ga_instance, solution, solution_idx: fitness(solution, tls_ids, offsets)
        
        self.ga_instance = ga.GA(num_generations=self.generations,
                                 num_parents_mating=self.mating_pool_size, 
                                 fitness_func=fitness_func,
                                 sol_per_pop=self.population, 
                                 num_genes=len(base_genome),
                                 parent_selection_type=self.selection_type,
                                 crossover_type=self.crossover_type,
                                 mutation_type=self.mutation_type,
                                 mutation_probability=self.mutation_probability,
                                 save_best_solutions=True)


    def execute(self, filename):
        """
        correr el GA con la configuracion cargada, mostrar y guardar resultados
        """
        self.ga_instance.run()
        self.ga_instance.save(filename)
        self.controller.save_solution()
        self.ga_instance.plot_fitness()
