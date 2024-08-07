"""
main del backend de SUMO, con y sin GUI
"""

import os
import sys
# import subprocess
import traci
import sumolib
import traci._trafficlight  
from sga import sga
import time


# configuracion para el controlador
USE_UI = True # cambiar a True para ver UI
CONFIG = "map.sumo.cfg" # .sumocfg or .sumo.cfg
PORT = 8813
SGA = sga()


# opcion para usar la UI
if USE_UI:
    SUMO_BINARY = "C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe"
else:
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")
    
    SUMO_BINARY = sumolib.checkBinary("sumo")
 
# iniciar conexion al simulador
traci.start(cmd=[SUMO_BINARY, "-c", CONFIG, "--start"], port=PORT) 

# ajustar la visualizacion si se utiliza
if USE_UI:
    traci.gui.setZoom("View #0", 10000)

# Avanzar la simulación hasta el final
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

traci.trafficlight.setParameter()

# cerrar conexion al simulador
traci.close()
