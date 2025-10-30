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
                 mating_pool_size = 7,
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


    def _setup_controller(self, controller): 
        """
        inicializar controlador
        """
        if not isinstance(controller, Controller):
            raise TypeError(
                f"controller debe ser una instancia de Controller, pero se recibió {type(controller).__name__}"
            )
        self.controller = controller
    

    def _setup_ga(self):
        """
        inicializar GA
        """

        def fitness(solution, tls_ids, offsets):
            """
            F = w1T1 + w2T2 
            donde: w1, w2 son los pesos y T1, T2 son tiempo en cola y tiempo de viaje
            """
            self.apply_solution(solution, tls_ids, offsets)
            veh_wt, veh_tt = self.controller.execute_simulation()

            T1 = self.calc_avg(veh_wt)
            T2 = self.calc_avg(veh_tt)
            w1 = 1
            w2 = 1

            F = w1*T1 + w2*T2 
            fitness = 1.0 / (F + 1e-6) 

            return fitness 
        
        tl_ids = self.get_tls_ids()
        base_genome, phase_counts = self.controller.build_genome(tl_ids)
        offsets = np.cumsum([0] + phase_counts)

        fitness_func = lambda ga_instance, solution, solution_idx: fitness(solution, tl_ids, offsets)
        
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


    def get_tls_ids(self):
        """
        retorna una lista con los ids de los semaforos
        """
        return self.controller.get_tl_ids()
    

    def calc_avg(self, data):
        """
        obtener el promedio de una lista
        """
        if data is None:
            return 0.0
        if len(data) == 0:
            return 0.0
        return float(np.mean(data))


    def apply_solution(self, solution, tls_ids, offsets): 
        """
        aplicar configuracion de semaforos encontrada por algoritmo a la network 
        """
        if len(solution) < (offsets[-1]):
            raise ValueError("Solution length does not match expected number of genes.")
        
        self.controller.reset()

        for i, tl_id in enumerate(tls_ids): 
            start, end = offsets[i], offsets[i+1] 
            durations = solution[start:end] 

            logic = self.controller.get_tl_logic(tl_id)
            new_phases = []

            for j, phase in enumerate(logic.phases):
                new_phases.append(self.controller.phase(phase, durations[j]))

            new_logic = self.controller.logic(logic, new_phases)
            self.controller.set_tl_logic(tl_id, new_logic)


    def execute(self, filename):
        """
        correr el GA con la configuracion cargada, mostrar y guardar resultados
        """
        self.ga_instance.run()
        self.ga_instance.save(filename)
        self.controller.save_solution()
        self.ga_instance.plot_fitness()

