"""
main del backend de SUMO, con y sin GUI
"""

import os
import sys
import traci
import sumolib
import traci._trafficlight  
from sga import sga
from controller import controller

if __name__ == '__main__':
    con = controller()
    sga_ = sga()

    con.start_sumo_conn()
    con.execute_simulation()
    con.close_sumo_conn()