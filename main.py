"""
main del backend de SUMO, con y sin GUI
"""

import os
import sys
import traci
import sumolib
import traci._trafficlight  
from sga import TlSga
from controller import Controller

if __name__ == '__main__':
    con = Controller(config='map.sumo.cfg')
    sga = TlSga(controller = con)

    # sga.run_simulation