"""
main del backend de SUMO, con y sin GUI
"""

from sga import TlSga
from controller import Controller


if __name__ == '__main__':
    con = Controller()
    con.start_sumo_conn()
    sga = TlSga(controller=con, 
                generations=80,
                population=12,
                mating_pool_size=4,
                selection_type="tournament",
                crossover_type="uniform",
                mutation_probability=0.15,
                get_initial_population=True)
    sga.execute(filename="auto")
    sga.controller.close_sumo_conn()
 