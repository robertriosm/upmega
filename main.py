"""
main del backend de SUMO, con y sin GUI
"""

from sga import TlSga
from controller import Controller


if __name__ == '__main__':
    con = Controller(config='map.sumo.cfg')
    sga = TlSga(controller = con, generations=5, solutions_per_population=5)
    sga.execute(filename="genetic")
    sga.controller.close_sumo_conn()