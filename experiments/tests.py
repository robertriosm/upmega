import os
import sys
# import sumolib
import traci
# import sumolib

SUMO_BINARY = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo.exe"
CONFIG = "map.sumo.cfg"

# Arrancar SUMO pausado (sin avanzar el tiempo)
traci.start([SUMO_BINARY, "-c", CONFIG, "--start", "--no-step-log", "true"])

# Leer datos sin avanzar la simulación
tl_ids = traci.trafficlight.getIDList()
# print("Semáforos:", tl_ids)

x1 = traci.simulation.getMinExpectedNumber()

# for tl in tl_ids:
#     logics = traci.trafficlight.getAllProgramLogics(tl)
#     print(f"{tl}: {logics} fases")

traci.simulation.saveState('initialstate.state.xml')

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

print('simulatioon terminada')

x2 = traci.simulation.getMinExpectedNumber()

traci.simulation.loadState('initialstate.state.xml')

x3 = traci.simulation.getMinExpectedNumber()

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

print('simulatioon terminada 2')

x4 = traci.simulation.getMinExpectedNumber()

# Cerrar conexión
traci.close()

# print("SUMO_HOME =", os.environ.get("SUMO_HOME"))
# tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
# print("tools =", tools)
# print("checkBinary sumo =", sumolib.checkBinary("sumo"))
# print("exists? sumo.exe =", os.path.exists(os.path.join(os.environ["SUMO_HOME"], "bin", "sumo.exe")))

# print("SUMO_HOME =", os.environ.get("SUMO_HOME"))

