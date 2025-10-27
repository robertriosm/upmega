import pygad
import numpy

# Parámetros para el problema de optimización
function_inputs = [4, -2, 3.5, 5, -11, -4.7]
desired_output = 44

# La función lambda debe aceptar los 3 argumentos requeridos
# y devolver un valor de fitness.
# Aquí se maximiza la aptitud haciendo 1.0 / (error + un valor pequeño).
fitness_lambda = lambda ga, solution, solution_idx: 1.0 / (numpy.abs(numpy.sum(solution * function_inputs) - desired_output) + 0.00000001)

# Parámetros para pygad.GA
ga_instance = pygad.GA(
    num_generations=50,
    num_parents_mating=4,
    fitness_func=fitness_lambda, # Usando la lambda aquí
    sol_per_pop=8,
    num_genes=len(function_inputs),
    init_range_low=-2,
    init_range_high=5,
    parent_selection_type="sss",
    crossover_type="single_point",
    mutation_type="random",
    mutation_percent_genes=10
)

# Ejecutar el algoritmo genético
ga_instance.run()

# Mostrar el mejor resultado
solution, solution_fitness, solution_idx = ga_instance.best_solution()
print(f"Mejor solución encontrada: {solution}")
print(f"Fitness de la mejor solución: {solution_fitness}")
