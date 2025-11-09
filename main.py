"""
main del backend de SUMO, con y sin GUI
"""

from sga import TlSga
from controller import Controller


if __name__ == '__main__':
    con = Controller()
    con.start_sumo_conn()
    sga = TlSga(controller=con, 
                generations=50, 
                population=10, 
                mating_pool_size=2, 
                selection_type="tournament",
                crossover_type="uniform",
                mutation_probability=0.1)
    sga.execute(filename="g50p10m2touruni")
    sga.controller.close_sumo_conn()
