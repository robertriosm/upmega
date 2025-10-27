"""
main del backend de SUMO, con y sin GUI
"""

from sga import TlSga
from controller import Controller


if __name__ == '__main__':
    con = Controller(config='map.sumo.cfg')
    sga = TlSga(controller = con, generations=10)
    sga.execute()
    sga.controller.close_sumo_conn()