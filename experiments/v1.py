import os
import sys
import traci
import sumolib
import tempfile

CONFIG = "map.sumo.cfg" 
PORT = 8813
NETWORK = "test.net.xml"
ROUTES = "map.rou.xml"

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    
SUMO_BINARY = sumolib.checkBinary("sumo") 

traci.start(cmd=[SUMO_BINARY, "-c", CONFIG], port=PORT)  

with tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8', suffix=".xml", delete_on_close=False) as temp_file:
    temp_file.close()

    traci.load(['-n', NETWORK, '-r', ROUTES, "--tripinfo", temp_file.name])

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

    with open(temp_file.name, 'r', encoding='utf-8') as f:
        content = f.read()

    temp_file.close()
        
traci.close()
