"""
main del backend de SUMO, con y sin GUI
"""

import os
import sys
# import subprocess
import traci
import sumolib
# import traci._trafficlight  
from sga import sga
import time


# configuracion para el controlador
USE_UI = False # cambiar a True para ver UI
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
    
    SUMO_BINARY = sumolib.checkBinary("sumo") # C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe 
    
# iniciar conexion al simulador
traci.start(cmd=[SUMO_BINARY, "-c", CONFIG, "--start"], port=PORT) 

# ajustar la visualizacion si se utiliza
if USE_UI:
    traci.gui.setZoom("View #0", 500)

file = open('results.txt', mode='w', encoding='utf')

# Avanzar la simulación hasta el final
while traci.simulation.getMinExpectedNumber() > 0:
    # time.sleep(0.1)
    traci.simulationStep()

# try:
#     traci.vehicle
#     traci.trafficlight
    # file.write(f'getIDList: {traci.trafficlight.getIDList().__repr__()}')
    # file.write('\n')
    # file.write(f'getControlledLinks: {traci.trafficlight.getControlledLinks('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getControlledLanes: {traci.trafficlight.getControlledLanes('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getSpentDuration: {traci.trafficlight.getSpentDuration('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getRedYellowGreenState: {traci.trafficlight.getRedYellowGreenState('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getAllContextSubscriptionResults: {traci.trafficlight.getAllContextSubscriptionResults().__repr__()}')
    # file.write('\n')
    # # file.write('getBlockingVehicles: traci.trafficlight.getBlockingVehicles().__repr__()')
    # file.write('\n')
    # # file.write(f'getNemaPhaseCalls: {traci.trafficlight.getNemaPhaseCalls('1438391835').__repr__()}')
    # file.write('\n')
    # # file.write('getPriorityVehicles: traci.trafficlight.getPriorityVehicles().__repr__()')
    # file.write('\n')
    # file.write(f'getAllProgramLogics: {traci.trafficlight.getAllProgramLogics('1438391835').__repr__()}') # deprecated -> getCompleteRedYellowGreenDefinition
    # file.write('\n')
    # file.write(f'getNextSwitch: {traci.trafficlight.getNextSwitch('1438391835').__repr__()}')
    # file.write('\n')
    # # file.write('getServedPersonCount: {traci.trafficlight.getServedPersonCount().__repr__()')
    # file.write('\n')
    # # file.write('getRivalVehicles: {traci.trafficlight.getRivalVehicles().__repr__()')
    # file.write('\n')
    # file.write(f'getCompleteRedYellowGreenDefinition: {traci.trafficlight.getCompleteRedYellowGreenDefinition('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getProgram: {traci.trafficlight.getProgram('1438391835').__repr__()}')
    # file.write('\n')
    # file.write(f'getIDCount: {traci.trafficlight.getIDCount().__repr__()}')
# except Exception as e: 
#     print('hubo error: ', e)
#     file.close()

# cerrar conexion al simulador
traci.close()
file.close()
