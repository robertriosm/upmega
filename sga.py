"""
implementacion de SGA con controlador
"""

import csv, json, sys
from datetime import datetime

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
                 mutation_probability = 0.1,
                 saturation = "saturate_10",
                 random_seed = None,
                 w1 = 1.0,
                 w2 = 1.1
                 ) -> None:
        self._setup_controller(controller)
        self._setup_config(population, generations, crossover_type,
                           mutation_type, mating_pool_size, selection_type,
                           mutation_probability, saturation,
                           random_seed, w1, w2)
        self._setup_ga()


    def _setup_config(self, population, generations, crossover_type,
                      mutation_type, mating_pool_size, selection_type, mutation_probability,
                      saturation, random_seed, w1, w2):
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
        self.stop_criteria = saturation
        self.random_seed = random_seed
        # los pesos viven aqui y no dentro de la funcion de fitness para poder
        # registrarlos: son parte de la definicion del problema, no un detalle
        self.w1 = w1
        self.w2 = w2
        # una fila por evaluacion, es el log que permite reconstruir la corrida
        self.evaluations = []


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

        def fitness(ga_instance, solution, tls_ids, gene_slices):
            """
            F = 1 / (w1T1 + w2T2)
            donde: w1, w2 son los pesos, T1 es tiempo de viaje y T2 tiempo en cola.
            Se invierte porque pygad maximiza y aqui se busca minimizar demoras.
            """
            sid = self.sid
            self.controller.apply_solution(solution, sid, tls_ids, gene_slices)
            durations, waiting_times, stats = self.controller.execute_simulation(sid)
            self.sid += 1 # aumentar como id unico

            # Sin normalizacion
            T1 = np.array(durations, dtype=np.float32)
            T2 = np.array(waiting_times, dtype=np.float32)

            T1_mean = np.mean(T1)
            T2_mean = np.mean(T2)

            F = 1 / (self.w1 * T1_mean + self.w2 * T2_mean + 1e-6)

            # log por evaluacion: sin esto, asociar un fitness con la red que lo
            # produjo obliga a reparsear todos los tripinfos a mano
            self.evaluations.append({
                "sid": sid,
                "generation": ga_instance.generations_completed,
                "fitness": float(F),
                "duration_mean": round(float(T1_mean), 3),
                "waiting_mean": round(float(T2_mean), 3),
                "time_loss": stats.get("timeLoss"),
                "speed": stats.get("speed"),
                "teleports": stats.get("teleports"),
                "vehicles": stats.get("count"),
            })

            # Con normalizacion
            # f1 = np.array(durations, dtype=np.float32)
            # f2 = np.array(waiting_times, dtype=np.float32)

            # f1_norm = (f1 - f1.min()) / (f1.max() - f1.min())
            # f2_norm = (f2 - f2.min()) / (f2.max() - f2.min())

            # f1_norm_mean = np.mean(f1_norm)
            # f2_norm_mean = np.mean(f2_norm)

            # F = w1 * f1_norm_mean + w2 * f2_norm_mean

            return F
    

        def build_gene_space(tls_ids):
            """
            un rango por gen, derivado de criterios de ingenieria de transito.

            - AMBAR: no es variable de decision. Su duracion la determina la
              velocidad de aproximacion (t_reaccion + v/2a), no el trafico, asi
              que se fija en su valor original. Son 166 de 386 fases que salen
              del espacio de busqueda y que ademas ya no se pueden volver
              inseguras.
            - TODO-ROJO: tiempo de despeje del cruce, [3,30).
            - VERDE: minimo de seguridad 7s, maximo 90s. Contiene los 39-82s
              que asigna netconvert y permite bajar lo suficiente para alcanzar
              los ciclos de 20-30s que da la formula de Webster con esta demanda.
            - OFFSET: desfase del inicio del ciclo, en porcentaje [0,100).

            Todos los valores por defecto de netconvert caen dentro de su rango:
            el punto de partida es factible, que es el objetivo de este diseno.
            """
            gene_space = []

            for tl in tls_ids:
                logic = self.controller.get_tl_logic(tl)

                for phase in logic.phases:
                    state = phase.state

                    # se pregunta primero por el verde: una fase con movimiento
                    # en verde es una fase verde aunque arrastre algun ambar
                    if 'G' in state or 'g' in state:
                        gene_space.append({'low': 7, 'high': 90})
                    elif 'y' in state: # transicion pura, fija por seguridad
                        gene_space.append(int(phase.duration))
                    else: # todo-rojo
                        gene_space.append({'low': 3, 'high': 30})

            # un offset por semaforo, al final del genoma
            gene_space += [{'low': 0, 'high': 100} for _ in tls_ids]

            return gene_space


        def on_gen_callback(ga_instance):
            """
            feedback del mejor fitness en la generacion
            """
            gen = ga_instance.generations_completed
            fit = ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1]
            print(f"Generation {gen} completed. Best fitness in this generation: {fit}")
        

        def gen_initial_pop(base):
            """
            el individuo 0 es SIEMPRE el genoma por defecto de netconvert: es el
            punto de partida contra el que se mide la mejora, no una opcion.
            El resto de la poblacion es aleatoria para dar diversidad.
            """
            initial_pop = [base]

            for _ in range(self.population - 1):
                # high es exclusivo, igual que el uniform(low, high) que usa
                # pygad al mutar. Los genes fijos (ambar) se copian tal cual
                individual = [np.random.randint(gs["low"], gs["high"]) if isinstance(gs, dict) else gs
                              for gs in self.gene_space]
                initial_pop.append(individual)

            return initial_pop
    

        base_genome, phase_counts = self.controller.build_genome()
        # indices de corte del tramo de duraciones, uno por semaforo.
        # Se llama gene_slices y no offsets para no confundirlo con el offset
        # del semaforo, que ahora es una variable de decision real
        gene_slices = np.cumsum([0] + phase_counts)
        tls_ids = self.controller.get_tl_ids() # garantizar la misma lista
        self.gene_space = build_gene_space(tls_ids)

        fitness_func = lambda ga_instance, solution, solution_idx: fitness(ga_instance, solution, tls_ids, gene_slices)

        initial_pop = gen_initial_pop(base_genome)

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
                                 on_generation=on_gen_callback,
                                 random_seed=self.random_seed,
                                 # ojo: si initial_pop != None, pygad ignora num_genes
                                 # y sol_per_pop y los deduce de initial_pop.shape
                                 initial_population=initial_pop)


    def execute(self, filename):
        """
        correr el GA con la configuracion cargada, mostrar y guardar resultados
        """
        if filename == "auto":
            st = self.selection_type[:3]
            ct = self.crossover_type[:3]
            P = int(self.mutation_probability*100)
            filename = f"g{self.generations}p{self.population}m{self.mating_pool_size}{st}{ct}P{P}"
        
        self.ga_instance.run()
        self.ga_instance.save(filename)
        self.write_run_record(filename)
        self.ga_instance.plot_fitness() # bloquea hasta cerrar la ventana, va de ultimo


    def write_run_record(self, filename):
        """
        deja en disco todo lo necesario para interpretar la corrida despues sin
        tener que abrir el .pkl ni reparsear los tripinfos.

        Escribe dos archivos:
        - {filename}.meta.json       configuracion completa, definicion del
                                     fitness y metricas agregadas de SUMO
        - {filename}.evaluations.csv una fila por simulacion ejecutada

        Y corre dos simulaciones extra con todas las salidas activadas: la red
        original como referencia fija y la mejor solucion encontrada. Son dos
        simulaciones, no mil, por eso ahi si se puede pedir el detalle completo.
        """
        best = max(self.evaluations, key=lambda e: e["fitness"]) if self.evaluations else None

        baseline_files, baseline_stats = self.controller.run_detailed(
            self.controller.NETWORK, f"{filename}.baseline")

        best_files, best_stats = {}, {}
        if best is not None:
            best_files, best_stats = self.controller.run_detailed(
                f"logics/{best['sid']}.net.xml", f"{filename}.best")

        ga_i = self.ga_instance

        meta = {
            "run": filename,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "versions": {
                "sumo": self.controller.get_sumo_version(),
                "pygad": getattr(ga, "__version__", None),
                "python": sys.version.split()[0],
            },
            "escenario": {
                "network": self.controller.NETWORK,
                "routes": self.controller.ROUTES,
                "template": self.controller.TEMPLATE,
                "sumo_seed": self.controller.SEED,
            },
            "fitness": {
                "formula": "F = 1 / (w1*duracion_media + w2*espera_media + 1e-6)",
                "w1": self.w1,
                "w2": self.w2,
                "sentido": "maximizar",
                "fuente": "tripinfo-output",
            },
            # se leen del objeto de pygad y no de self: esto es lo que realmente
            # corrio, no lo que se pidio. Con initial_population, pygad
            # sobreescribe num_genes y sol_per_pop con la forma del array
            "ga": {
                "num_generations": ga_i.num_generations,
                "sol_per_pop": ga_i.sol_per_pop,
                "num_genes": ga_i.num_genes,
                "num_parents_mating": ga_i.num_parents_mating,
                "parent_selection_type": ga_i.parent_selection_type,
                "K_tournament": ga_i.K_tournament,
                "crossover_type": ga_i.crossover_type,
                "crossover_probability": ga_i.crossover_probability,
                "mutation_type": ga_i.mutation_type,
                "mutation_probability": ga_i.mutation_probability,
                "keep_elitism": ga_i.keep_elitism,
                "keep_parents": ga_i.keep_parents,
                "stop_criteria": ga_i.stop_criteria,
                "random_seed": self.random_seed,
                "poblacion_inicial": "individuo 0 = genoma por defecto de netconvert, resto aleatorio",
                "gene_space": {
                    "genes": len(self.gene_space),
                    "genes_fijos": sum(1 for g in self.gene_space if not isinstance(g, dict)),
                    "rangos": sorted({(g["low"], g["high"]) for g in self.gene_space
                                      if isinstance(g, dict)}),
                },
            },
            "resultado": {
                "generaciones_completadas": ga_i.generations_completed,
                "detenido_por": ("stop_criteria"
                                 if ga_i.generations_completed < ga_i.num_generations
                                 else "presupuesto de generaciones agotado"),
                "evaluaciones": len(self.evaluations),
                "mejor_fitness": best["fitness"] if best else None,
                "mejor_generacion": best["generation"] if best else None,
                "mejor_sid": best["sid"] if best else None,
                "red_de_la_mejor": f"logics/{best['sid']}.net.xml" if best else None,
            },
            "metricas": {
                "baseline": baseline_stats,
                "mejor": best_stats,
                "mejora_pct": {
                    k: round((1 - best_stats[k] / baseline_stats[k]) * 100, 2)
                    for k in ("duration", "waitingTime", "timeLoss", "departDelay")
                    if baseline_stats.get(k) and best_stats.get(k)
                },
            },
            "archivos": {
                "modelo": f"{filename}.pkl",
                "evaluaciones": f"{filename}.evaluations.csv",
                "detalle_baseline": baseline_files,
                "detalle_mejor": best_files,
            },
        }

        with open(f"{filename}.meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False, default=str)

        if self.evaluations:
            with open(f"{filename}.evaluations.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(self.evaluations[0].keys()))
                writer.writeheader()
                writer.writerows(self.evaluations)

        print(f"registro escrito: {filename}.meta.json  |  {filename}.evaluations.csv")
