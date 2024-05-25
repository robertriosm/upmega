"""
controlador del backend de SUMO, con y sin GUI
"""

import os
import sys
# import subprocess
import traci
import sumolib
import traci._trafficlight  
from sga import sga

USE_UI = False
# USE_UI = True


if USE_UI:
    SUMO_BINARY = "C:/Program Files (x86)/Eclipse/Sumo/bin/sumo-gui.exe"
else:
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        sys.exit("please declare environment variable 'SUMO_HOME'")
    
    SUMO_BINARY = sumolib.checkBinary("sumo")
    

CONFIG = "map.sumo.cfg" # .sumocfg or .sumo.cfg
PORT = 8813
SGA = sga()

traci.start(cmd=[SUMO_BINARY, "-c", CONFIG, "--start"], port=PORT) 

if USE_UI:
    traci.gui.setZoom("View #0", 1000)
 
sga.get_semaphores(127, "before")

# Avanza la simulación hasta el final
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

did = traci.trafficlight.DOMAIN_ID
lights = traci.trafficlight.getAllContextSubscriptionResults()

sga.get_semaphores(127, "after")

traci.close()
