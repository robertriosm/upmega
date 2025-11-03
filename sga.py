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
        self.gene_type = int
        self.sid = 0
        self.stop_criteria = "saturate_5"


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
            self.controller.apply_solution(solution, self.sid, tls_ids, offsets)
            durations, waiting_times = self.controller.execute_simulation(self.sid)
            self.sid += 1 # aumentar como id unico

            w1 = 0.9
            w2 = 1.1

            T1 = np.array(durations, dtype=np.float32)
            T2 = np.array(waiting_times, dtype=np.float32)

            T1_mean = np.mean(T1)
            T2_mean = np.mean(T2)

            F = 1 / (w1 * T1_mean + w2 * T2_mean + 1e-6) 

            return F
    

        def build_gene_space(tls_ids):
            """
            genera un espacio donde los genes pueden mutar con restricciones al amarillo
            """
            gene_space = []

            for tl in tls_ids:
                logic = self.controller.get_tl_logic(tl)
                
                for phase in logic.phases:
                    state = phase.state

                    # Clasificacion de fase
                    if 'y' in state.lower():  # contiene amarillo
                        gene_space.append({'low': 3, 'high': 6})
                    else:  # verdes u otras combinaciones
                        gene_space.append({'low': 7, 'high': 80})

            return gene_space


        def on_gen_callback(ga_instance):
            """
            feedback del mejor fitness en la generacion
            """
            gen = ga_instance.generations_completed
            fit = ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1]
            print(f"Generation {gen} completed. Best fitness in this generation: {fit}")
    

        base_genome, phase_counts = self.controller.build_genome()
        offsets = np.cumsum([0] + phase_counts) # garantizar la misma lista
        tls_ids = self.controller.get_tl_ids() # garantizar la misma lista 
        self.gene_space = build_gene_space(tls_ids)
        print(self.gene_space)

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
                                 gene_space=self.gene_space,
                                 gene_type=self.gene_type,
                                 stop_criteria=self.stop_criteria,
                                 on_generation=on_gen_callback)


    def execute(self, filename):
        """
        correr el GA con la configuracion cargada, mostrar y guardar resultados
        """
        self.ga_instance.run()
        self.ga_instance.save(filename)
        self.ga_instance.plot_fitness()
