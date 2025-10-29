# controller.py
import os
import traci
import random


class Controller2:
    def __init__(self, config="map.sumo.cfg", binary=None, port=8813):
        self.CONFIG = config
        self.PORT = port
        self.SUMO_BINARY = binary or r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"

    def start(self):
        cmd = [self.SUMO_BINARY, "-c", self.CONFIG, "--start", "--no-warnings", "true"]
        traci.start(cmd, port=self.PORT)

    def stop(self):
        traci.close()

    def run_simulation(self):
        """Ejecuta la simulación completa y devuelve el tiempo promedio de espera."""
        total_wait = 0
        count = 0

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            for vid in traci.vehicle.getIDList():
                try:
                    w = traci.vehicle.getWaitingTime(vid)
                    total_wait += w
                    count += 1
                except traci.TraCIException:
                    continue

        return total_wait / count if count > 0 else 0.0

    def set_tl_green_time(self, tls_id, green_time):
        """Modifica la duración de la fase verde."""
        logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
        new_phases = []
        for ph in logic.phases:
            if "G" in ph.state:
                new_phases.append(traci.trafficlight.Phase(green_time, ph.state))
            else:
                new_phases.append(ph)
        new_logic = traci.trafficlight.Logic("0", 0, 0, new_phases)
        traci.trafficlight.setProgramLogic(tls_id, new_logic)

# sga.py

class SimpleGA:
    def __init__(self, pop_size, generations, min_val, max_val, fitness_func):
        self.pop_size = pop_size
        self.generations = generations
        self.min_val = min_val
        self.max_val = max_val
        self.fitness_func = fitness_func

    def evolve(self):
        # Crear población inicial
        population = [random.uniform(self.min_val, self.max_val) for _ in range(self.pop_size)]

        for gen in range(self.generations):
            fitness_scores = [self.fitness_func(x) for x in population]
            best_idx = fitness_scores.index(min(fitness_scores))  # menor = mejor (tiempo)
            best = population[best_idx]

            print(f"Gen {gen}: mejor verde = {best:.2f}s, fitness = {fitness_scores[best_idx]:.2f}")

            # Selección simple: top 2 padres
            sorted_pop = [x for _, x in sorted(zip(fitness_scores, population))]
            parents = sorted_pop[:2]

            # Cruzamiento y mutación
            children = []
            for _ in range(self.pop_size - 2):
                p1, p2 = random.sample(parents, 2)
                child = (p1 + p2) / 2 + random.uniform(-2, 2)
                child = max(self.min_val, min(self.max_val, child))
                children.append(child)

            population = parents + children

        return best

# main.py

def fitness_func(green_time):
    ctrl = Controller2("map.sumo.cfg")
    ctrl.start()

    try:
        tls_id = traci.trafficlight.getIDList()[0]  # usa el primer semáforo
        ctrl.set_tl_green_time(tls_id, green_time)
        avg_wait = ctrl.run_simulation()
    finally:
        ctrl.stop()

    return avg_wait  # menor es mejor

if __name__ == "__main__":
    ga = SimpleGA(
        pop_size=5,
        generations=3,
        min_val=10,   # segundos
        max_val=60,
        fitness_func=fitness_func
    )

    best_green = ga.evolve()
    print(f"\n✅ Mejor duración verde encontrada: {best_green:.2f} segundos")
