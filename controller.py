"""
dedicado a la interaccion con SUMO y comunicacion con backend
"""


import os
import sys
# import subprocess
import traci
import sumolib
import traci._trafficlight  
from sga import sga
import time


class controller:
    def __init__(self, config = "./map.sumo.cfg", use_ui = False, port = 8813) -> None:
        self.USE_UI = use_ui # cambiar a True para ver UI
        self.CONFIG = config # .sumocfg or .sumo.cfg
        self.PORT = port
        self.SGA = sga()
        self.SUMO_BINARY = self.get_sumo_binary()

    def get_sumo_binary(self):
        # opcion para usar la UI
        if self.USE_UI:
            self.SUMO_BINARY = "C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe"
        else:
            if 'SUMO_HOME' in os.environ:
                tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
                sys.path.append(tools)
            else:
                sys.exit("please declare environment variable 'SUMO_HOME'")
            
            self.SUMO_BINARY = sumolib.checkBinary("sumo") # C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe 


    def start_sumo_conn(self):
        traci.start(cmd=[self.SUMO_BINARY, "-c", self.CONFIG, "--start"], port=self.PORT) 
    

    def get_trafficlights_data(self):
        pass 

    def execute_simulation(self):
        # Avanzar la simulación hasta el final
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()


    def close_sumo_conn(self):
        traci.close()

