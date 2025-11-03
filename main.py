"""
main del backend de SUMO, con y sin GUI
"""

from sga import TlSga
from controller import Controller


if __name__ == '__main__':
    con = Controller()
    con.start_sumo_conn()
    sga = TlSga(controller = con, generations=2, population=4, mating_pool_size=2)
    sga.execute(filename="g50p20m8")
    sga.controller.close_sumo_conn()
