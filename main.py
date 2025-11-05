"""
main del backend de SUMO, con y sin GUI
"""

from sga import TlSga
from controller import Controller


if __name__ == '__main__':
    con = Controller()
    con.start_sumo_conn()
    sga = TlSga(controller = con, 
                generations=20, 
                population=10, 
                mating_pool_size=5, 
                selection_type="tournament",
                crossover_type="uniform")
    sga.execute(filename="g20p10m5touruni")
    sga.controller.close_sumo_conn()
