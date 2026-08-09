"""
main del backend de SUMO, con y sin GUI
"""

import argparse

import demand
from sga import TlSga
from controller import Controller


def parse_args():
    parser = argparse.ArgumentParser(
        description="Optimizacion de tiempos de semaforo con un SGA sobre SUMO")
    parser.add_argument("--num-of-cars", type=int, default=None, metavar="N",
                        help="cantidad de vehiculos a generar para la simulacion. "
                             "Si se omite se usa el archivo de rutas por defecto")
    parser.add_argument("--demand-seed", type=int, default=42, metavar="S",
                        help="semilla de randomTrips al generar la demanda (default 42)")
    parser.add_argument("--regenerate", action="store_true",
                        help="regenerar la demanda aunque el archivo ya exista")
    parser.add_argument("--workers", type=int, default=6, metavar="W",
                        help="simulaciones SUMO en paralelo (default 6, los nucleos fisicos "
                             "de esta maquina: medido, de 6 en adelante no acelera mas). "
                             "Cada una es un proceso aislado, asi que cambia el tiempo pero "
                             "no los resultados. Usar 1 para correr secuencial")
    parser.add_argument("--saturation", type=int, default=None, metavar="K",
                        help="detener la corrida si el mejor fitness no mejora en K "
                             "generaciones seguidas. Si se omite no hay paro anticipado "
                             "y la corrida agota las generaciones configuradas")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    routes, demand_info = "map.rou.xml", None
    if args.num_of_cars:
        routes, demand_info = demand.generate(args.num_of_cars,
                                              seed=args.demand_seed,
                                              force=args.regenerate)
        print(f"demanda: {demand_info['generados']} vehiculos de "
              f"{demand_info['solicitados']} solicitados -> {routes}")

    con = Controller(routes=routes, demand=demand_info)
    con.start_sumo_conn()
    sga = TlSga(controller=con,
                generations=150,
                population=30,
                mating_pool_size=12,
                k_tournament=5,
                selection_type="tournament",
                crossover_type="uniform",
                mutation_probability=0.02,
                workers=args.workers,
                random_seed=42,
                saturation=f"saturate_{args.saturation}" if args.saturation else None)
    sga.execute(filename="auto")
    sga.controller.close_sumo_conn()
